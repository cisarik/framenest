"""Dual-prefix environment identity resolver for ADR-0085.

One setting name may be spelled with either accepted prefix during the ordered
Kronika identity cut sequence:

- ``KRONIKA_<SUFFIX>`` is the identity prefix recorded by ADR-0085.
- ``FRAMENEST_<SUFFIX>`` is the compatible spelling that every installed
  release, the installed ``/etc/framenest/framenest.env`` file, and the
  installed systemd units still use.

This module is the only place that reads either spelling, so readers learn the
new spelling while writers keep emitting the old one until the matching reader
is the installed release.

Precedence, exactly:

===========================  =========================  =========================
``KRONIKA_<SUFFIX>``         ``FRAMENEST_<SUFFIX>``     Result
===========================  =========================  =========================
set                          unset                      the ``KRONIKA_`` value
unset                        set                        the ``FRAMENEST_`` value
unset                        unset                      ``None``; caller default
set                          set, identical             that value
set                          set, different             fail closed
===========================  =========================  =========================

A variable set to the empty string counts as unset, so the installed
environment file and existing systemd ``Environment=`` handling keep their
current meaning.

The fail-closed path raises :class:`IdentityEnvironmentConflictError`, which
carries the setting-name suffix only. It never carries, derives, or logs a
value, a length, a hash, or a ``repr`` of either value, and it never returns a
partially resolved pair.
"""

from __future__ import annotations

import os
from typing import Mapping

PRIMARY_ENVIRONMENT_PREFIX = "KRONIKA_"
COMPATIBLE_ENVIRONMENT_PREFIX = "FRAMENEST_"

#: Process exit status a command line entry point uses for a fail-closed
#: identity-environment conflict.
EXIT_IDENTITY_ENVIRONMENT_CONFLICT = 2


class IdentityEnvironmentConflictError(Exception):
    """Both accepted prefixes set one setting name to different values.

    The exception carries the setting-name suffix only. Callers translate it
    into their own sanitized error type; the message text is already safe to
    print because it names the two variables and nothing about their values.
    """

    def __init__(self, suffix: str) -> None:
        self.suffix = suffix
        super().__init__(
            f"Conflicting environment variables {PRIMARY_ENVIRONMENT_PREFIX}{suffix} "
            f"and {COMPATIBLE_ENVIRONMENT_PREFIX}{suffix} are set to different values."
        )


def identity_environment_names(suffix: str) -> tuple[str, str]:
    """Return both accepted variable names for one setting-name suffix."""
    return (
        f"{PRIMARY_ENVIRONMENT_PREFIX}{suffix}",
        f"{COMPATIBLE_ENVIRONMENT_PREFIX}{suffix}",
    )


def canonical_identity_environment(values: Mapping[str, str]) -> dict[str, str]:
    """Present a mapping under canonical variable names.

    ``pydantic-settings`` lowercases the keys it reads from an environment file,
    so a file mapping cannot be handed to :func:`lookup_env` directly. This
    helper keeps only the entries that carry an accepted identity prefix, under
    the canonical upper-case spelling, and drops everything else. Values that
    carry no accepted prefix are outside the identity surface.
    """
    canonical: dict[str, str] = {}
    prefixes = (PRIMARY_ENVIRONMENT_PREFIX, COMPATIBLE_ENVIRONMENT_PREFIX)
    for key, value in values.items():
        upper = key.upper()
        for prefix in prefixes:
            if upper.startswith(prefix):
                canonical[f"{prefix}{upper[len(prefix):]}"] = value
                break
    return canonical


def lookup_env(
    suffix: str,
    *,
    environ: Mapping[str, str] | None = None,
) -> str | None:
    """Return the resolved value of one prefixed setting name.

    ``suffix`` is the part of the variable name after the prefix, for example
    ``DATABASE_PATH``. ``environ`` exists for the readers that already accept an
    explicit environment mapping so they can resolve without mutating the
    process environment; it defaults to :data:`os.environ`.

    Returns ``None`` when neither spelling carries a non-empty value, which is
    the caller's own default. Raises
    :class:`IdentityEnvironmentConflictError` when both spellings are set to
    different values, before either value is returned.
    """
    env = os.environ if environ is None else environ
    primary = env.get(f"{PRIMARY_ENVIRONMENT_PREFIX}{suffix}")
    compatible = env.get(f"{COMPATIBLE_ENVIRONMENT_PREFIX}{suffix}")
    if primary == "":
        primary = None
    if compatible == "":
        compatible = None
    if primary is None:
        return compatible
    if compatible is None or primary == compatible:
        return primary
    raise IdentityEnvironmentConflictError(suffix)
