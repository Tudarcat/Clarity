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

from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text
from typing import Optional, Callable, Protocol
from agent.provider.provider_base import StreamingPart


class StreamingCallbackProtocol(Protocol):
    streaming: bool
    full_content: str
    full_reasoning: str

    def start(self) -> None: ...
    def stop(self) -> None: ...
    def __call__(self, part: StreamingPart) -> None: ...
    def get_full_content(self) -> str: ...
    def get_full_reasoning(self) -> str: ...
    def reset(self) -> None: ...


class StreamingCallback:
    """
    Callback handler for streaming output with Rich Live display.
    """

    def __init__(self, console: Console, streaming: bool = True):
        self.console = console
        self.streaming = streaming
        self.full_content = ""
        self.full_reasoning = ""
        self._live: Optional[Live] = None

    def start(self):
        """Start the Live display."""
        if self.streaming:
            self._live = Live(
                "Thinking...",
                console=self.console,
                refresh_per_second=10,
                transient=False
            )
            self._live.start()

    def stop(self):
        """Stop the Live display and cleanup."""
        if self._live:
            self._live.stop()
            self._live = None

    def __call__(self, part: StreamingPart):
        """
        Handle a streaming part. Called for each chunk of the streaming response.

        :param part: The StreamingPart containing delta content.
        """
        if not self.streaming:
            return

        updated = False

        if part.reasoning_delta:
            self.full_reasoning += part.reasoning_delta
            updated = True

        if part.content_delta:
            self.full_content += part.content_delta
            updated = True

        if updated and self._live:
            self._update_display()

    def _update_display(self):
        """Update the Live display with current content."""
        if not self._live:
            return

        content_parts = []

        if self.full_reasoning:
            content_parts.append(Text("Reasoning:\n", style="bold magenta"))
            content_parts.append(Text(self.full_reasoning, style="dim magenta"))
            if self.full_content:
                content_parts.append(Text("\n\n", style=""))

        if self.full_content:
            content_parts.append(Text("Content:\n", style="bold green"))
            try:
                content_parts.append(Markdown(self.full_content))
            except:
                content_parts.append(Text(self.full_content, style=""))

        if content_parts:
            self._live.update(Group(*content_parts))
        else:
            self._live.update("Thinking...")

    def get_full_content(self) -> str:
        """Get the accumulated full content."""
        return self.full_content

    def get_full_reasoning(self) -> str:
        """Get the accumulated full reasoning content."""
        return self.full_reasoning

    def reset(self):
        """Reset all accumulated content."""
        self.full_content = ""
        self.full_reasoning = ""
        if self._live:
            self._live.update("Thinking...")


class NonStreamingCallback:
    """
    Non-streaming callback that simply collects content for later display.
    """

    def __init__(self, console: Console):
        self.console = console
        self.streaming = False
        self.full_content = ""
        self.full_reasoning = ""

    def start(self):
        """No-op for non-streaming."""
        pass

    def stop(self):
        """No-op for non-streaming."""
        pass

    def __call__(self, part: StreamingPart):
        """
        Handle a streaming part by accumulating content.

        :param part: The StreamingPart containing delta content.
        """
        if part.reasoning_delta:
            self.full_reasoning += part.reasoning_delta

        if part.content_delta:
            self.full_content += part.content_delta

    def get_full_content(self) -> str:
        """Get the accumulated full content."""
        return self.full_content

    def get_full_reasoning(self) -> str:
        """Get the accumulated full reasoning content."""
        return self.full_reasoning

    def reset(self):
        """Reset all accumulated content."""
        self.full_content = ""
        self.full_reasoning = ""


def create_streaming_callback(console: Console, streaming: bool) -> StreamingCallbackProtocol:
    """
    Factory function to create the appropriate streaming callback.

    :param console: Rich Console instance.
    :param streaming: Whether streaming mode is enabled.
    :return: Either StreamingCallback or NonStreamingCallback.
    """
    if streaming:
        return StreamingCallback(console)
    else:
        return NonStreamingCallback(console)