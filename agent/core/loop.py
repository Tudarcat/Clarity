from typing import List, Dict, Any, Callable, Optional
from agent.provider.provider_base import ProviderBase, LLMResponse
from agent.core.message import MessageBuilder
from agent.tool import ToolBase

class LoopResult:
    def __init__(self, final_answer: str, messages: List[Dict[str, Any]]):
        self.final_answer = final_answer
        self.messages = messages

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
                 thinking_callback: Optional[Callable[[], None]] = None) -> LoopResult:

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
            # Call thinking callback before making the API call
            if thinking_callback:
                thinking_callback()
            
            response = self.provider.chat(messages, tool_schemas)
            
            if response.has_tool_calls():
                progress_callback(response)
                messages = self._handle_tool_calls(messages, response)
            else:
                progress_callback(response)
                final_answer = response.content
                return LoopResult(final_answer=final_answer, messages=messages)
        
        return LoopResult(final_answer="", messages=messages)

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
