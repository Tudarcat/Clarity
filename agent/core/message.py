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
2. You should call appropriate tools to obtain specific, detailed, and accurate information - never attempt to guess or fabricate information.
3. After calling a tool, make full use of the retrieved results in your responses.
4. When you modify files, always verify that the changes are correct.
5. If a tool call fails, carefully examine the reason and attempt to call it again.
6. Avoid falling into logical loops; if you determine that a task cannot be completed, promptly disengage from it.
7. Refrain from generating text that contains emotional content, explicit political stances, or racial issues - you are a neutral agent.
8. When you search for papers based on a keyword, you should try multiple similar keywords, 
including keywords in both English and the language used by the user, to ensure the search is as comprehensive and thorough as possible.
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