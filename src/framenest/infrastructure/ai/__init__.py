"""Infrastructure adapters for AI-assisted media suggestion prototypes."""

from framenest.infrastructure.ai.nvidia_nim import NvidiaNimMediaSuggestionProvider
from framenest.infrastructure.ai.vercel_gateway import VercelAiGatewayMediaSuggestionProvider

__all__ = ["NvidiaNimMediaSuggestionProvider", "VercelAiGatewayMediaSuggestionProvider"]
