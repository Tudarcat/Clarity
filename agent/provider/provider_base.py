'''
   Copyright 2026 Yunda Wu

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''


from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass
import asyncio

@dataclass
class StreamingPart:
    """
    A dataclass to represent a part of a streaming response.
    """
    reasoning_delta: Optional[str] = None
    content_delta: Optional[str] = None

    def __init__(self, reasoning_delta: Optional[str] = None, content_delta: Optional[str] = None):
        self.reasoning_delta = reasoning_delta
        self.content_delta = content_delta

@dataclass
class LLMResponse:
    """
    A dataclass to represent the response from a language model provider.
    """
    reasoning_content: Optional[str] = None
    content: Optional[str] = None
    stop_reason: Optional[str] = None
    tool_calls: Optional[list[Dict[str, Any]]] = None
    token_usage: Optional[Dict[str, int]] = None

    def has_tool_calls(self) -> bool:
        """
        Check if the response contains tool calls.

        :return: True if the response contains tool calls, False otherwise.
        """
        return self.tool_calls is not None and len(self.tool_calls) > 0

class ProviderBase(ABC):
    """
    Base class for all providers. 
    All providers must inherit from this class and implement the required methods.
    """

    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url

    @abstractmethod
    def chat(self, messages: list[Dict[str, Any]], 
             tool_list: list[Dict[str, Any]] = [], 
             streaming: bool = False, 
             stream_callback: Optional[Callable[[StreamingPart], None]] = None) -> LLMResponse:
        """
        Abstract method to send a chat message to the provider and receive a response.
        Must be implemented by all subclasses.

        :param messages: A list of messages to send to the provider.
        :param tool_list: A list of tools available for use.
        :param streaming: Whether to enable streaming mode.
        :param stream_callback: A callback to be called for each part of the streaming response.
        :return: A LLMResponse object containing the provider's response.
        """
        pass

    async def achat(self, messages: list[Dict[str, Any]], 
                    tool_list: list[Dict[str, Any]] = [], 
                    streaming: bool = False, 
                    stream_callback: Optional[Callable[[StreamingPart], None]] = None) -> LLMResponse:
        """
        Async method to send a chat message to the provider and receive a response.
        Default implementation wraps the sync chat() method in asyncio.to_thread().
        Subclasses should override this with a native async implementation if possible.

        :param messages: A list of messages to send to the provider.
        :param tool_list: A list of tools available for use.
        :param streaming: Whether to enable streaming mode.
        :param stream_callback: A callback to be called for each part of the streaming response.
        :return: A LLMResponse object containing the provider's response.
        """
        return await asyncio.to_thread(self.chat, messages, tool_list, streaming, stream_callback)

    def replace_empty_content(self, response: LLMResponse) -> LLMResponse:
        """
        Replace empty content with reasoning content if available.

        :param response: The LLMResponse object to process.
        :return: The processed LLMResponse object.
        """
        if response.content is None or response.content.strip() == "":
            response.content = "(empty)"
        return response

    @abstractmethod
    def get_max_tokens(self) -> int:
        """
        Abstract method to get the maximum number of tokens the provider can handle.
        Must be implemented by all subclasses.

        :return: The maximum number of tokens.
        """
        pass