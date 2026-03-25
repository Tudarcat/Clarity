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

"""
This module provides the MessageBuilder class for building messages for the agent system.
"""

import os
import platform
import locale
from datetime import datetime
from typing import List, Dict, Any

class MessageBuilder:
    def __init__(self, work_dir: str):
        self.work_dir = work_dir
    
    def build_system_message(self) -> str:
        text = self._get_agent_identity() + self._get_runtime_prompt(self.work_dir)
        return text

    def _get_agent_identity(self) -> str:
        """
        Get the identity of the agent.
        
        :return: A string containing the agent identity.
        """
        identity = f"""
# Identity

## You
You are Clarity, an AI assistant designed to help users with academic paper retrieval, translation, comprehension, summarization, note-taking, and organization.

## Policy
1. You are an intelligent agent with tool-calling capabilities and can invoke tools when needed.
2. Call tools ONLY when you need external information (e.g., searching papers, reading files, scraping web pages). 
   - DO NOT call tools for questions about your own identity, capabilities, or general knowledge you already possess.
   - DO NOT call tools for simple greetings or casual conversation.
   - DO NOT call tools that are not existing.
3. You should call appropriate tools to obtain specific, detailed, and accurate information - never attempt to guess or fabricate information.
4. After calling a tool, make full use of the retrieved results in your responses.
5. When you modify files, always verify that the changes are correct.
6. If a tool call fails, carefully examine the reason and attempt to call it again.
7. Avoid falling into logical loops; if you determine that a task cannot be completed, promptly disengage from it.
8. Refrain from generating text that contains emotional content, explicit political stances, or racial issues - you are a neutral agent.
9. When you search for papers based on a keyword, you should try multiple similar keywords, 
including keywords in both English and the language used by the user, to ensure the search is as comprehensive and thorough as possible.
10. For complex tasks, you can plan and execute the task in 3-5 stages to ensure thorough completion. You can use UpdateTaskTool to update the task status after each stage. 
11. After invoking the paper search tool, you must provide a comprehensive summary of the retrieved information. This summary must explicitly include the Paper Title, Authors, Publication Date, and most critically, the DOI (Digital Object Identifier).
        """
        return identity

    def _get_runtime_prompt(self, work_dir: str) -> str:
        """
        Get runtime information including current time, timezone, OS, and language.
        
        :param work_dir: The working directory.
        :return: A string containing runtime information.
        """
        now = datetime.now()
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        import time
        timezone_name = time.tzname[0]
        if time.daylight:
            timezone_name = time.tzname[1]
        utc_offset = time.strftime("%z")
        
        os_name = platform.system()
        os_version = platform.version()
        os_release = platform.release()
        
        lang = locale.getdefaultlocale()[0]
        if not lang:
            lang = "Unknown"
        
        cwd = os.getcwd()
        
        prompt = f"""Current Runtime Information:
- Current Time: {time_str}
- Timezone: {timezone_name} (UTC{utc_offset})
- Operating System: {os_name} {os_release}
- OS Version: {os_version}
- Language: {lang}
- Working Directory: {cwd}"""
        
        return prompt

    def add_agent_message(self, messages: list[dict], 
                          role: str, content: str,
                          tool_calls: List[Dict[str, Any]] | None = None):
        mesg = {"role": role, "content": content}
        if tool_calls:
            mesg["tool_calls"] = tool_calls
        messages.append(mesg)
        return messages

    def add_tools_result_message(self, messages: list[dict],
                                 tool_call_id: str,
                                 tool_result: str):
        messages.append({"role": "tools", "content": tool_result,
                         "tool_call_id": tool_call_id})
        return messages

    @staticmethod
    def compress_messages(messages: list[dict], max_tokens: int) -> list[dict]:
        """
        Compress the messages to fit within the max_tokens limit.
        
        :param messages: The list of messages to compress.
        :param max_tokens: The maximum number of tokens allowed.
        :return: The compressed list of messages.
        """
        # TODO: Implement message compression logic
        return messages