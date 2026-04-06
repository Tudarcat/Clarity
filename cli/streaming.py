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

from rich.console import Console
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
    Callback handler for streaming output using direct console append (no Live).
    Avoids cursor position issues when scrolling.
    Markdown is rendered only in non-streaming mode for perfect formatting.
    """

    def __init__(self, console: Console, streaming: bool = True):
        self.console = console
        self.streaming = streaming
        self.full_content = ""
        self.full_reasoning = ""
        self._reasoning_printed = False
        self._content_printed = False

    def start(self):
        """Start the streaming display."""
        if self.streaming:
            self.console.print(Text("Thinking:", style="bold magenta"))

    def stop(self):
        """
        Stop the streaming display.
        In streaming mode, ensures proper line ending.
        Markdown is not rendered in streaming mode to avoid scroll issues.
        """
        if self.streaming and (self._reasoning_printed or self._content_printed):
            self.console.print()

    def __call__(self, part: StreamingPart):
        """
        Handle a streaming part by directly printing deltas.

        :param part: The StreamingPart containing delta content.
        """
        if not self.streaming:
            return

        if part.reasoning_delta:
            self.full_reasoning += part.reasoning_delta
            if not self._reasoning_printed:
                #self.console.print(Text("Thinking:\n", style="bold magenta"), end="")
                self._reasoning_printed = True
            self.console.print(Text(part.reasoning_delta, style="dim magenta"), end="")

        if part.content_delta:
            self.full_content += part.content_delta
            if not self._content_printed:
                if self._reasoning_printed:
                    self.console.print("\n")
                self.console.print(Text("Assistant:\n", style="bold green"), end="")
                self._content_printed = True
            self.console.print(part.content_delta, end="")

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
        self._reasoning_printed = False
        self._content_printed = False


class NonStreamingCallback:
    """
    Non-streaming callback that simply collects content for later display.
    Renders perfect Markdown when displayed via OutputFormatter.
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