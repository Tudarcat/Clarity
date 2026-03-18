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
from agent.provider.provider_base import ProviderBase, LLMResponse


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
            reasoning_effort: str = "") -> LLMResponse:
        """
        Send a chat message to the custom provider and receive a response.

        :param messages: A list of messages to send to the provider.
        :param tool_list: A list of tools available for use.
        :return: A LLMResponse object containing the provider's response.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tool_list if tool_list else None
        )
        
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

    def get_max_tokens(self) -> int:
        """
        Get the maximum number of tokens the provider can handle.

        :return: The maximum number of tokens.
        """
        return 256 * 1000