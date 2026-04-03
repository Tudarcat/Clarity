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

from typing import List, Dict, Any, Callable, Optional
import asyncio
from agent.provider.provider_base import ProviderBase, LLMResponse, StreamingPart
from agent.core.message import MessageBuilder
from agent.tool import ToolBase

class LoopResult:
    def __init__(self, final_answer: str, messages: List[Dict[str, Any]], token_usage: Optional[Dict[str, int]] = None):
        self.final_answer = final_answer
        self.messages = messages
        self.token_usage: Optional[Dict[str, int]] = token_usage


class ReActLoop:
    def __init__(self, provider: ProviderBase,
                 context: MessageBuilder,
                 tools: List[ToolBase] | None = None,
                 max_iter: int = 20,
                 ):
        self.provider = provider
        self.context = context
        self.tools = tools or []
        self.max_iter = max_iter
        self.is_running = False
        self._tool_map: Dict[str, ToolBase] = {}
        
        for tool in self.tools:
            self._tool_map[tool.name] = tool


    def run_loop(self, messages: List[Dict[str, Any]], 
                 progress_callback: Callable[[LLMResponse], None],
                 thinking_callback: Optional[Callable[[], None]] = None, 
                 streaming: bool = False,
                 stream_callback: Optional[Any] = None
                 ) -> LoopResult:

        """
        Run the ReAct loop with the given messages.

        :param messages: A list of messages to send to the provider.
        :param progress_callback: A callback function to call with each response.
        :param thinking_callback: A callback function to call when the model starts thinking.
        :return: The response from the provider.
        """
        self.is_running = True
        tool_schemas = [tool.to_openai_tool() for tool in self.tools]
        
        for _ in range(self.max_iter):
            if stream_callback and hasattr(stream_callback, "reset"):
                stream_callback.reset()
            
            if thinking_callback:
                thinking_callback()
            
            response = self.provider.chat(messages, tool_schemas, streaming, stream_callback)
            
            if stream_callback and hasattr(stream_callback, "stop"):
                stream_callback.stop()
            
            if response.has_tool_calls():
                progress_callback(response)
                messages = self._handle_tool_calls(messages, response)
                
                if stream_callback and hasattr(stream_callback, "start"):
                    stream_callback.start()
            else:
                progress_callback(response)
                final_answer = response.content
                return LoopResult(final_answer=final_answer, messages=messages, token_usage=response.token_usage)
        
        return LoopResult(final_answer="", messages=messages, token_usage=response.token_usage)

    async def arun_loop(self, messages: List[Dict[str, Any]], 
                        progress_callback: Callable[[LLMResponse], None],
                        thinking_callback: Optional[Callable[[], None]] = None, 
                        streaming: bool = False,
                        stream_callback: Optional[Any] = None
                        ) -> LoopResult:
        """
        Async version of run_loop. Run the ReAct loop with the given messages.

        :param messages: A list of messages to send to the provider.
        :param progress_callback: A callback function to call with each response.
        :param thinking_callback: A callback function to call when the model starts thinking.
        :return: The response from the provider.
        """
        self.is_running = True
        tool_schemas = [tool.to_openai_tool() for tool in self.tools]
        
        for _ in range(self.max_iter):
            if stream_callback and hasattr(stream_callback, "reset"):
                stream_callback.reset()
            
            if thinking_callback:
                thinking_callback()
            
            response = await self.provider.achat(messages, tool_schemas, streaming, stream_callback)
            
            if stream_callback and hasattr(stream_callback, "stop"):
                stream_callback.stop()
            
            if response.has_tool_calls():
                progress_callback(response)
                messages = await self._ahandle_tool_calls(messages, response)
                
                if stream_callback and hasattr(stream_callback, "start"):
                    stream_callback.start()
            else:
                progress_callback(response)
                final_answer = response.content
                return LoopResult(final_answer=final_answer, messages=messages, token_usage=response.token_usage)
        
        return LoopResult(final_answer="", messages=messages, token_usage=response.token_usage)

    async def _ahandle_tool_calls(self, messages: List[Dict[str, Any]], 
                           response: LLMResponse) -> List[Dict[str, Any]]:
        """
        Async version of _handle_tool_calls. Handle tool calls from the LLM response.

        :param messages: The current message list.
        :param response: The LLM response containing tool calls.
        :return: Updated message list with tool results.
        """
        if not response.tool_calls:
            return messages

        messages.append({
            "role": "assistant",
            "content": response.content,
            "tool_calls": response.tool_calls
        })

        for tool_call in response.tool_calls:
            tool_name = tool_call.get("function", {}).get("name")
            tool_args = tool_call.get("function", {}).get("arguments", {})
            tool_call_id = tool_call.get("id")

            if tool_name in self._tool_map:
                tool = self._tool_map[tool_name]
                try:
                    if isinstance(tool_args, str):
                        import json
                        tool_args = json.loads(tool_args)
                    
                    result = await tool.aexecute(**tool_args)
                except Exception as e:
                    result = f"Error executing tool '{tool_name}': {str(e)}"
            else:
                result = f"Tool '{tool_name}' not found"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": result
            })

        return messages

    def _handle_tool_calls(self, messages: List[Dict[str, Any]], 
                           response: LLMResponse) -> List[Dict[str, Any]]:
        """
        Handle tool calls from the LLM response.

        :param messages: The current message list.
        :param response: The LLM response containing tool calls.
        :return: Updated message list with tool results.
        """
        if not response.tool_calls:
            return messages

        messages.append({
            "role": "assistant",
            "content": response.content,
            "tool_calls": response.tool_calls
        })

        for tool_call in response.tool_calls:
            tool_name = tool_call.get("function", {}).get("name")
            tool_args = tool_call.get("function", {}).get("arguments", {})
            tool_call_id = tool_call.get("id")

            if tool_name in self._tool_map:
                tool = self._tool_map[tool_name]
                try:
                    if isinstance(tool_args, str):
                        import json
                        tool_args = json.loads(tool_args)
                    
                    result = tool.execute(**tool_args)
                except Exception as e:
                    result = f"Error executing tool '{tool_name}': {str(e)}"
            else:
                result = f"Tool '{tool_name}' not found"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": result
            })

        return messages
