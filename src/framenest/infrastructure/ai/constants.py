"""Constants for the initial NVIDIA NIM prototype adapter."""

from __future__ import annotations

DEFAULT_PROVIDER_ID = "nvidia-nim"
DEFAULT_MODEL_ID = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
NVIDIA_CHAT_COMPLETIONS_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

MAX_MODEL_ID_LENGTH = 120
MAX_REQUEST_BODY_BYTES = 24 * 1024 * 1024
MAX_RESPONSE_BODY_BYTES = 1 * 1024 * 1024
REQUEST_TIMEOUT_SECONDS = 120
MAX_TOKENS = 2048
TEMPERATURE = 0.2
