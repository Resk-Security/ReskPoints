import functools
import inspect
import time
from typing import Any, Callable, TypeVar

from .agent_logger import AgentLogger
from .models import ActionLog

F = TypeVar("F", bound=Callable[..., Any])


def log_action(
    agent_id: str | None = None,
    action_name: str | None = None,
    logger: AgentLogger | None = None,
    capture_params: bool = True,
    capture_result: bool = True,
    **extra_metadata: Any,
) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        _action_name = action_name or func.__name__
        module = inspect.getmodule(func)
        module_name = module.__name__ if module else ""

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _logger = logger or _get_default_logger()
            _agent_id = agent_id or _resolve_agent_id(func)
            t0 = time.time()
            parameters: dict[str, Any] = {}
            if capture_params:
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                parameters = dict(bound.arguments)
                for k, v in parameters.items():
                    if hasattr(v, "__dict__"):
                        parameters[k] = f"<{type(v).__name__}>"
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - t0) * 1000
                _logger.log(
                    agent_id=_agent_id,
                    action=f"{module_name}.{_action_name}",
                    probability=1.0,
                    params=parameters,
                    result=result if capture_result else None,
                    success=True,
                    duration_ms=duration,
                    **extra_metadata,
                )
                return result
            except Exception as e:
                duration = (time.time() - t0) * 1000
                _logger.log(
                    agent_id=_agent_id,
                    action=f"{module_name}.{_action_name}",
                    probability=1.0,
                    params=parameters,
                    result=str(e),
                    success=False,
                    duration_ms=duration,
                    **extra_metadata,
                )
                raise

        return wrapper  # type: ignore

    return decorator


_default_logger: AgentLogger | None = None


def _get_default_logger() -> AgentLogger:
    global _default_logger
    if _default_logger is None:
        _default_logger = AgentLogger()
    return _default_logger


def _resolve_agent_id(func: Callable[..., Any]) -> str:
    return f"{func.__module__}.{func.__qualname__}"
