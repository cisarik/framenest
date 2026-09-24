export const PROTO_VERSION = 1;

export const PACK_VERSION = 5;

export const EXTENSION_VERSION = "0.1.0";

export const ENGINE_VERSION = "0.1.0";

// Removed modes are not advertised. Plain ask is the only offered job.
export const CLIENT_CAPABILITIES = ["durable_submission", "admin_resume"];

export const PROGRESS_PHASES = [
  "accepted",
  "project",
  "tab_ready",
  "new_chat",
  "mode",
  "composed",
  "sent",
  "observing",
  "project_warning",
  "cleanup_warning",
];

export const ERROR_CODES = [
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
];
