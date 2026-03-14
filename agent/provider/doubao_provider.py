import os
from openai import OpenAI
from agent.provider.provider_base import ProviderBase, LLMResponse


class DoubaoProvider(ProviderBase):

    def __init__(self, api_key: str, api_url: str, model: str = ""):
        """
        Initialize the DoubaoProvider with the given API key, URL, and model.

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

    def chat(self, messages: list[dict], tool_list: list[dict]) -> LLMResponse:
        """
        Send a chat message to the Doubao provider and receive a response.

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
        
        return LLMResponse(content=content, tool_calls=tool_calls, reasoning_content=reasoning_content)
