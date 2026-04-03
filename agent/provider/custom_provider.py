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


import os
from openai import OpenAI
from agent.provider.provider_base import ProviderBase, LLMResponse, StreamingPart
from typing import Optional, Callable


class CustomProvider(ProviderBase):

    def __init__(self, api_key: str, api_url: str, model: str = ""):
        """
        Initialize the CustomProvider with the given API key, URL, and model.

        :param api_key: The API key for authentication.
        :param api_url: The base URL for the API.
        :param model: The model name to use.
        """
        
        super().__init__(api_key, api_url)
        self.model = model

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_url
        )

    def chat(self, messages: list[dict], tool_list: list[dict], 
             streaming: bool = False, 
             stream_callback: Optional[Callable[[StreamingPart], None]] = None) -> LLMResponse:
        """
        Send a chat message to the custom provider and receive a response.

        :param messages: A list of messages to send to the provider.
        :param tool_list: A list of tools available for use.
        :param streaming: Whether to enable streaming mode.
        :param stream_callback: A callback to be called for each part of the streaming response.
        :return: A LLMResponse object containing the provider's response.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tool_list if tool_list else None,
            stream=streaming,
            stream_options={"include_usage": True}
        )
        
        if not streaming:
            # Non-streaming mode
            choice = response.choices[0]
            content = choice.message.content or ""
            tool_calls = None
            reasoning_content = None
            
            if hasattr(choice.message, 'reasoning_content') and choice.message.reasoning_content:
                reasoning_content = choice.message.reasoning_content
            
            if choice.message.tool_calls:
                tool_calls = []
                for tc in choice.message.tool_calls:
                    tool_calls.append({
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    })
            
            token_usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return LLMResponse(content=content, tool_calls=tool_calls, reasoning_content=reasoning_content, token_usage=token_usage)
        else:
            # Streaming mode
            full_content = ""
            full_reasoning_content = ""
            full_tool_calls = []
            total_tokens: int = 0
            temp_tool_calls_map = {}

            for chunk in response:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                if hasattr(chunk, "usage") and chunk.usage:
                    total_tokens += chunk.usage.total_tokens
                
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    r_content = delta.reasoning_content
                    full_reasoning_content += r_content
                    r_part = StreamingPart(reasoning_delta=r_content)
                    if stream_callback:
                        stream_callback(r_part)
                
                if hasattr(delta, "content") and delta.content:
                    c_content = delta.content
                    full_content += c_content
                    c_part = StreamingPart(content_delta=c_content)
                    if stream_callback:
                        stream_callback(c_part)
                
                if hasattr(delta, "tool_calls") and delta.tool_calls:
                    for tc in delta.tool_calls:
                        index = tc.index
                        if index not in temp_tool_calls_map:
                            temp_tool_calls_map[index] = {
                                "id": tc.id or "",
                                "type": tc.type or "function",
                                "function": {
                                    "name": tc.function.name if tc.function and tc.function.name else "",
                                    "arguments": ""
                                }
                            }
                        if tc.function and tc.function.arguments:
                            temp_tool_calls_map[index]["function"]["arguments"] += tc.function.arguments
                        if tc.id:
                            temp_tool_calls_map[index]["id"] = tc.id
                        if tc.function and tc.function.name:
                            temp_tool_calls_map[index]["function"]["name"] = tc.function.name

            # After processing all chunks
            sorted_indices = sorted(temp_tool_calls_map.keys())
            for idx in sorted_indices:
                full_tool_calls.append(temp_tool_calls_map[idx])
            
            return LLMResponse(content=full_content, tool_calls=full_tool_calls, reasoning_content=full_reasoning_content, token_usage={"total_tokens": total_tokens})

    def get_max_tokens(self) -> int:
        """
        Get the maximum number of tokens the provider can handle.

        :return: The maximum number of tokens.
        """
        return 256 * 1000