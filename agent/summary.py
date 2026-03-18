from agent.provider.provider_base import ProviderBase

class Summary:
    def __init__(self, provider: ProviderBase):
        self.provider = provider

    def _summarize(self, message: list[dict]) -> str:
        """
        Summarize the message.
        
        :param message: The message to summarize.
        :return: The summarized message.
        """
        # TODO: Implement summary logic
        return ""

    def _get_summary_prompt(self, messages: list[dict]) -> str:
        """
        Get the summary prompt.
        
        :param messages: The list of messages to summarize.
        :return: The summary prompt.
        """
        prompt = """
# Task: Dialogue History Compression and Key Information Extraction

You are an efficient dialogue summarizer. Your task is to compress the input dialogue history into a high information-density summary, which can replace the original history for continued LLM reference.

# Input Format
A multi-turn dialogue will be provided. Each turn includes both the user's input and the LLM Agent's response.

# Output Requirements
Please generate a **structured summary report** containing the following two parts:

**1. Core Fact Extraction (Key Information)**

*   **Confirmed Facts**: List all entity information confirmed during the dialogue. Examples: person names, article/literature titles, dates, specific numerical values, preference choices, etc.
*   **User's Core Objective**: Summarize in one sentence what the user aims to achieve through the Agent.
*   **Completed Steps**: Provide a bullet-point list of key actions that have been executed (e.g., password verified, report draft generated).
*   **Pending/To-be-Confirmed Items**: Provide a bullet-point list of matters still waiting or not yet completed.

**2. Dialogue Context Summary (Maintaining Coherence)**

*   Summarize each semantically complete dialogue turn. If multiple consecutive turns discuss the same sub-topic, they can be merged into a single summary entry.
*   Summaries should connect the reasoning logic, rather than being a chronological log.

# Constraints

*   **Ignore Internal Details**: Remove specific parameters of tool calls and API request processes. However, if a tool returns important data (such as API query results), that data should be included in the "Core Facts."
*   **Length Control**: The total output length should be controlled to 20%~30% of the original text. If the original text is extremely short (<200 Tokens), preserve the key information completely without forced compression.
*   **Fidelity**: It is strictly forbidden to add information that does not exist in the dialogue. If speculation is necessary, it must be noted as "[speculation]".

        """
        return prompt

    def summarize(self, messages: list[dict]) -> str:
        """
        Summarize the messages.
        
        :param messages: The list of messages to summarize.
        :return: The summarized message.
        """
        # TODO: Implement summary logic
        return ""