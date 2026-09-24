EXIT_OK = 0
EXIT_USAGE = 2
EXIT_BRIDGE = 3
EXIT_JOB_FAILED = 4
EXIT_TIMEOUT = 5
EXIT_CANCELLED = 6
EXIT_INTERVENTION = 7
EXIT_PROTO = 8

ERROR_CODES = (
    "E_BROWSER_UNAVAILABLE",
    "E_NEEDS_ADMIN",
    "E_SERVICE_LIMIT",
    "E_IDEMPOTENCY_CONFLICT",
    "E_AMBIGUOUS_SEND",
    "E_JOURNAL_UNAVAILABLE",
    "E_PROTO_MISMATCH",
    "E_NO_TAB",
    "E_TAB_GONE",
    "E_LOGIN_REQUIRED",
    "E_CAPTCHA_REQUIRED",
    "E_CONSENT_REQUIRED",
    "E_LIMIT_REACHED",
    "E_COMPOSER_NOT_FOUND",
    "E_INPUT_FAILED",
    "E_SEND_NOT_READY",
    "E_SEND_FAILED",
    "E_UPLOAD_FAILED",
    "E_ATTACHMENT_MISSING",
    "E_RESPONSE_TIMEOUT",
    "E_RESPONSE_EMPTY",
    "E_RESULT_TOO_LARGE",
    "E_STALL",
    "E_FILE_MISSING",
    "E_FILE_TOO_LARGE",
    "E_BUSY",
    "E_CANCELLED",
    "E_INTERVENTION_TIMEOUT",
    "E_PROJECT_NOT_CONFIGURED",
    "E_PROJECT_UNAVAILABLE",
    "E_WEB_SEARCH_UNAVAILABLE",
    "E_DEEP_RESEARCH_UNAVAILABLE",
    "E_CONVERSATION_UNAVAILABLE",
    "E_INTERNAL",
)

_ERROR_EXIT_CODES = {
    "E_RESPONSE_TIMEOUT": EXIT_TIMEOUT,
    "E_CANCELLED": EXIT_CANCELLED,
    "E_INTERVENTION_TIMEOUT": EXIT_INTERVENTION,
    "E_PROTO_MISMATCH": EXIT_PROTO,
}


def exit_code_for_error(code: str | None) -> int:
    return _ERROR_EXIT_CODES.get(code or "", EXIT_JOB_FAILED)


def safe_message(code: str) -> str:
    return {
        "E_BUSY": "A task is already active.",
        "E_BROWSER_UNAVAILABLE": "The browser is unavailable.",
        "E_NEEDS_ADMIN": "Administrator intervention is required.",
        "E_SERVICE_LIMIT": "Capture capacity is exhausted.",
        "E_IDEMPOTENCY_CONFLICT": "The request identity conflicts with retained content.",
        "E_AMBIGUOUS_SEND": "Submission association is uncertain; do not resend.",
        "E_JOURNAL_UNAVAILABLE": "Durable capture state is unavailable.",
        "E_RESPONSE_TIMEOUT": "The active response time limit expired.",
        "E_RESULT_TOO_LARGE": "The complete result exceeds the delivery byte limit.",
        "E_INTERVENTION_TIMEOUT": "The administrator wait limit expired.",
        "E_CANCELLED": "The task was cancelled.",
    }.get(code, "The capture request could not be completed.")
