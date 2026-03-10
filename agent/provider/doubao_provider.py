import os
from openai import OpenAI
from agent.provider.provider_base import ProviderBase, LLMResponse


class DoubaoProvider(ProviderBase):

    def __init__(self, api_key: str, api_url: str):
        """
        Initialize the DoubaoProvider with the given API key and URL.
        """
        
        super().__init__(api_key, api_url)

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_url
        )

    def chat(self, messages: list[dict], tool_list: list[dict]) -> dict:
        """
        Send a chat message to the Doubao provider and receive a response.

        :param messages: A list of messages to send to the provider.
        :param tool_list: A list of tools available for use.
        :return: A dictionary containing the provider's response.
        """
        response = self.client.chat.completions.create(
            model="ep-20260310201337-5k45l",
            messages=messages,
        )
        return response.dict()