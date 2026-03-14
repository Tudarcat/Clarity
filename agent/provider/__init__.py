"""
This module provides the base classes and utilities for the agent provider.
"""
from agent.provider.provider_base import ProviderBase, LLMResponse
from agent.provider.doubao_provider import DoubaoProvider

__all__ = [
    "ProviderBase",
    "LLMResponse",
    "DoubaoProvider"
]

provider_type = {
    "doubao": DoubaoProvider
}