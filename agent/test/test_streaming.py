import os
from openai import OpenAI

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass

from agent.tool.tool_base import ToolSchema, ToolParameter, ToolBase


class TestEchoTool(ToolBase):
    """
    A simple test tool that echoes back the parameters it receives.
    """

    @property
    def name(self) -> str:
        return "test_echo"

    @property
    def description(self) -> str:
        return "A test tool that echoes back the parameters it receives."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="message",
                type="string",
                description="Message to echo",
                required=True
            ),
            ToolParameter(
                name="number",
                type="integer",
                description="Number to echo",
                required=False,
                default=0
            ),
            ToolParameter(
                name="flag",
                type="boolean",
                description="Flag to echo",
                required=False,
                default=True
            )
        ]

    def execute(self, **kwargs) -> str:
        """
        Execute the test tool and print the parameters.
        
        :param kwargs: The parameters for the tool.
        :return: A string containing the echoed parameters.
        """
        print("\n=== TestEchoTool Called ===")
        print("Received parameters:")
        for key, value in kwargs.items():
            print(f"  {key}: {value}")
        print("========================")
        
        # Return the parameters as a string
        param_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        return f"Echoed: {param_str}"

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
             tool_list: list[Dict[str, Any]] = []) -> LLMResponse:
        """
        Abstract method to send a chat message to the provider and receive a response.
        Must be implemented by all subclasses.

        :param messages: A list of messages to send to the provider.
        :param tool_list: A list of tools available for use.
        :return: A LLMResponse object containing the provider's response.
        """
        pass




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
        Send a chat message to the custom provider and receive a streaming response.
        Prints content as it arrives.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tool_list if tool_list else None,
            stream=True,  # 关键：开启流式
            stream_options={"include_usage": True}
        )
        
        full_content = ""
        full_reasoning_content = ""
        full_tool_calls = []
        temp_tool_calls_map = {} # 用于在流式过程中临时拼接工具调用的分片 (index -> data)
        
        # 用于追踪是否正在打印推理内容或普通内容，以便添加标签
        has_printed_reasoning_header = False
        has_printed_content_header = False

        print("-" * 20 + " Streaming Start " + "-" * 20)

        test_usage_str = ""

        for chunk in response:
            if(hasattr(chunk, 'usage')):
                if(chunk.usage):
                    test_usage_str += f"Tokens: {chunk.usage.total_tokens} "
            else:
                test_usage_str += f"Tokens: 0 "
            
            if not chunk.choices:
                continue
                
            delta = chunk.choices[0].delta
            
            # assume reasoning_content is in delta.reasoning_content

            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                r_content = delta.reasoning_content
                full_reasoning_content += r_content
                if not has_printed_reasoning_header:
                    print("\n[Thinking]: ", end="", flush=True)
                    has_printed_reasoning_header = True
                print(r_content, end="", flush=True)

            # content
            if delta.content:
                content_chunk = delta.content
                full_content += content_chunk
                if not has_printed_content_header and not has_printed_reasoning_header:
                    # 如果没有推理内容，直接打印普通内容
                    print("\n[Response]: ", end="", flush=True)
                    has_printed_content_header = True
                elif has_printed_reasoning_header and not has_printed_content_header:
                    # 如果刚结束推理，开始打印普通内容
                    print("\n[Response]: ", end="", flush=True)
                    has_printed_content_header = True
                
                print(content_chunk, end="", flush=True)

            # tool_calls
            if delta.tool_calls:
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
                    
                    # 拼接参数
                    if tc.function and tc.function.arguments:
                        temp_tool_calls_map[index]["function"]["arguments"] += tc.function.arguments
                    
                    # 更新 ID 和 Name
                    if tc.id:
                        temp_tool_calls_map[index]["id"] = tc.id
                    if tc.function and tc.function.name:
                        temp_tool_calls_map[index]["function"]["name"] = tc.function.name

        # save to tool call list
        sorted_indices = sorted(temp_tool_calls_map.keys())
        for idx in sorted_indices:
            full_tool_calls.append(temp_tool_calls_map[idx])

        print("\n" + "-" * 20 + " Streaming End " + "-" * 20)
        print(test_usage_str)
        
        return LLMResponse(
        content=full_content, 
        tool_calls=full_tool_calls if full_tool_calls else None, 
        reasoning_content=full_reasoning_content if full_reasoning_content else None, 
        token_usage=chunk.usage if chunk.usage else None
        )


if __name__ == "__main__":
    # Create provider
    api_key = os.getenv("ARK_API_KEY")
    custom_provider = CustomProvider(api_key, "https://ark.cn-beijing.volces.com/api/v3",
        "doubao-seed-code-preview-251028")
    
    # Test 1: Basic streaming response
    print("=== Test 1: Basic streaming response ===")
    message = [
        {"role": "user", "content": "你好"}
    ]
    response = custom_provider.chat(messages= message, tool_list=[])
    print(response)
    
    # Test 2: Streaming with tool call
    print("\n=== Test 2: Streaming with tool call ===")
    # Create test tool
    test_tool = TestEchoTool()
    # Convert tool to OpenAI format
    tool_schema = test_tool.to_openai_tool()
    
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Use the test_echo tool to echo back the user's message."
        },
        {
            "role": "user",
            "content": "Please call test_echo with message 'Hello from test', number 42, and flag true"
        }
    ]
    
    response = custom_provider.chat(messages=messages, tool_list=[tool_schema])
    print("\nFinal response:")
    print(response)
    
    # If tool calls were made, execute the tool
    if response.has_tool_calls():
        print("\nExecuting tool calls...")
        print(f"Total tool calls: {len(response.tool_calls)}")
        for tool_call in response.tool_calls:
            tool_name = tool_call.get("function", {}).get("name")
            tool_args = tool_call.get("function", {}).get("arguments")
            
            if tool_name == "test_echo":
                import json
                try:
                    args_dict = json.loads(tool_args)
                    result = test_tool.execute(**args_dict)
                    print(f"Tool execution result: {result}")
                except Exception as e:
                    print(f"Error executing tool: {str(e)}")
