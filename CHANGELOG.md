# Changelog

## [0.1.3] - 2026-10-25

### Fixed
- OpenTelemetry is now selectable from `reskpoints.yaml`; it was missing from
  the platform registry, so `platforms.opentelemetry.enabled: true` was ignored.
- The `mock` platform can be enabled explicitly.
- A configuration without an enabled platform now logs a warning instead of
  silently discarding events in the in-memory mock.
- `__version__` matches the package version.
