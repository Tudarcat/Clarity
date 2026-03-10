from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass

@dataclass
class LLMResponse:
    """
    A dataclass to represent the response from a language model provider.
    """
    content: str
    tool_calls: Optional[list[Dict[str, Any]]] = None

class ProviderBase(ABC):
    """
    Base class for all providers. 
    All providers must inherit from this class and implement the required methods.
    """

    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url

    @abstractmethod
    async def chat(self, messages: list[Dict[str, Any]], 
                   tool_list: list[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Abstract method to send a chat message to the provider and receive a response.
        Must be implemented by all subclasses.

        :param messages: A list of messages to send to the provider.
        :param tool_list: A list of tools available for use.
        :return: A dictionary containing the provider's response.
        """
        pass