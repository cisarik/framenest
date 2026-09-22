"""Local loopback bridge between the operator CLI and the headless page driver.

Modules:

- ``store``: durable bridge state under an explicit state directory.
- ``auth``: per-install token and loopback Host/Origin checks.
- ``jobs``: one-flight ask lifecycle, cancellation, and transient text results.
- ``server``: the loopback HTTP API on ``127.0.0.1`` only.
"""
