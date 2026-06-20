import argparse
import json
import sys
from pathlib import Path

from .agent_logger import AgentLogger
from .config import AgentLoggerConfig


def cmd_log(args):
    logger = AgentLogger(args.config)
    params = {}
    if args.params:
        params = json.loads(args.params)
    result = None
    if args.result:
        result = json.loads(args.result)
    results = logger.log(
        agent_id=args.agent_id,
        action=args.action,
        probability=args.probability,
        params=params,
        result=result,
        success=args.success,
    )
    print(json.dumps([r.to_dict() for r in results], indent=2))
    any_fail = any(not r.success for r in results)
    return 1 if any_fail else 0


def cmd_test(args):
    logger = AgentLogger(args.config)
    print(f"Testing agent logging on {len(logger.platforms)} platform(s)...")
    print()
    for name, platform in logger.platforms.items():
        entry = _test_entry()
        result = platform.emit(entry)
        status = "✓" if result.success else "✗"
        dur = f"{result.duration_ms:.1f}ms" if result.duration_ms else "?"
        print(f"  [{status}] {name:15s} {dur:>10s}  {result.error or ''}")
    print()
    print("Health:")
    for pname, h in logger.health().items():
        print(f"  {pname:15s} status={h['status']} queue={h['queue_size']}")
    return 0


def cmd_status(args):
    logger = AgentLogger(args.config)
    print(f"ReskPoints Agent Logger — {logger.environment}")
    print(f"Host: {logger.host}")
    print(f"Platforms: {len(logger.platforms)}")
    print()
    print(f"{'Platform':<20s} {'Status':<12s} {'Queue':<8s} {'Error':<30s}")
    print("-" * 70)
    for pname, h in logger.health().items():
        print(f"{pname:<20s} {h['status']:<12s} {h['queue_size']:<8d} {h.get('error', '') or '':<30s}")
    return 0


def cmd_tail(args):
    logger = AgentLogger(args.config)
    console = logger.get_platform("console")
    if console is None:
        print("error: console platform not enabled", file=sys.stderr)
        return 1
    print(f"Live tailing logs (Ctrl+C to stop)...")
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


def cmd_replay(args):
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1
    logger = AgentLogger(args.config)
    count = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            from .models import ActionLog
            entry = ActionLog.from_dict(data)
            logger.log_action(entry)
            count += 1
    print(f"Replayed {count} log entries")
    return 0


def _test_entry():
    from .models import ActionLog
    return ActionLog(
        agent_id="test-agent",
        action="test_action",
        probability=0.95,
        parameters={"test": True, "value": 42},
        result="ok",
        success=True,
    )


def main():
    parser = argparse.ArgumentParser(
        description="ReskPoints Agent Action Logger CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config", "-c",
        default="reskpoints.yaml",
        help="Path to config YAML (default: reskpoints.yaml)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # log
    log_p = subparsers.add_parser("log", help="Log an agent action")
    log_p.add_argument("--agent-id", required=True, help="Agent identifier")
    log_p.add_argument("--action", required=True, help="Action name")
    log_p.add_argument("--probability", type=float, default=1.0, help="Action probability")
    log_p.add_argument("--params", help="JSON string of parameters")
    log_p.add_argument("--result", help="JSON string of result")
    log_p.add_argument("--success", action="store_true", default=True, help="Success flag")

    # test
    test_p = subparsers.add_parser("test", help="Test all platforms")

    # status
    subparsers.add_parser("status", help="Show platform health")

    # tail
    subparsers.add_parser("tail", help="Live tail logs (console)")

    # replay
    replay_p = subparsers.add_parser("replay", help="Replay logs from a file")
    replay_p.add_argument("file", help="Path to JSONL file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "log": cmd_log,
        "test": cmd_test,
        "status": cmd_status,
        "tail": cmd_tail,
        "replay": cmd_replay,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
