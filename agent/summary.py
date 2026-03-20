from typing import List, Dict, Any
from agent.provider.provider_base import ProviderBase

class Summary:
    def __init__(self, provider: ProviderBase):
        self.provider = provider

    def _build_summary_message(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build the summary message.
        
        :param messages: The list of messages to build summary from.
        :return: The summary message.
        """
        dialogue_text = ""
        for message in messages:
            role = message["role"]
            content = message.get("content", "")
            if message.get("tool_calls"):
                tool_names = [t.get("function", {}).get("name") for t in message.get("tool_calls", [])]
                content += f" Tool Calls: {tool_names}"
            dialogue_text += f"{role}: {content}\n"
        summary_prompt = f"""
# Task: Dialogue History Compression and Key Information Extraction

You are an efficient dialogue summarizer. Your task is to compress the input dialogue history into a high information-density summary.

# Dialogue History to Summarize:
{dialogue_text}

# {self._get_summary_instructions()}
"""
        
        return [
            {"role": "system", "content": "You are a precise dialogue summarizer."},
            {"role": "user", "content": summary_prompt}
        ]

    def _get_summary_instructions(self) -> str:
        """
        Get the summary instructions.
        """
        return """
# Output Requirements
Please generate a **structured summary report** containing the following two parts:

**1. Core Fact Extraction (Key Information)**
- **Confirmed Facts**: List all entity information confirmed during the dialogue. Examples: person names, article/literature titles, dates, specific numerical values, preference choices, etc.
- **User's Core Objective**: Summarize in one sentence what the user aims to achieve through the Agent.
- **Completed Steps**: Provide a bullet-point list of key actions that have been executed.
- **Pending/To-be-Confirmed Items**: Provide a bullet-point list of matters still waiting or not yet completed.

**2. Dialogue Context Summary (Maintaining Coherence)**
- Summarize each semantically complete dialogue turn. If multiple consecutive turns discuss the same sub-topic, merge them into a single summary entry.
- Summaries should connect the reasoning logic, rather than being a chronological log.

# Constraints
- **Ignore Internal Details**: Remove specific parameters of tool calls. But important tool results should be included in "Confirmed Facts".
- **Length Control**: Keep the summary concise but comprehensive.
- **Fidelity**: Do not add information not present in the dialogue.
"""

    def summarize(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Summarize the messages.
        
        :param messages: The list of messages to summarize.
        :return: The summarized message.
        """
        summary_messages = self._build_summary_message(messages)
        try:
            response = self.provider.chat(messages=summary_messages)
            summary_content = response.content
            compressed_messages = [
                {"role": "system", "content": f"[Dialogue has been compressed.] There are compressed messages. {summary_content} . Please continue the conversation based on the compressed messages."}
            ]
            if len(messages) >= 4:
                compressed_messages += messages[-3:]
            else:
                compressed_messages += messages
            return compressed_messages
        except Exception as e:
            print(f"Error summarizing messages: {e}")
            return messages
