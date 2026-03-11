"""
Main CLI application for Clarity Agent.
"""

import os
import sys
import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich import print as rprint

from agent.provider.provider_base import LLMResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.provider import DoubaoProvider
from agent.core.loop import ReActLoop, LoopResult
from agent.core.message import MessageBuilder
from agent.tool import ReadFileTool, WriteFileTool, EditFileTool, ListDirectoryTool

app = typer.Typer(
    name="clarity",
    help="Clarity Agent - An intelligent assistant CLI tool"
)

console = Console()


class OutputFormatter:
    """
    Formatter for different types of agent output.
    """
    
    @staticmethod
    def print_think(content: str):
        """
        Print thinking content with a distinct style.
        """
        console.print("\n")
        console.print(Panel(
            Markdown(content),
            title="[bold blue]💭 Thinking[/bold blue]",
            border_style="blue",
            padding=(1, 2)
        ))
    
    @staticmethod
    def print_content(content: str):
        """
        Print regular content.
        """
        console.print("\n")
        console.print(Panel(
            Markdown(content),
            title="[bold green]📝 Response[/bold green]",
            border_style="green",
            padding=(1, 2)
        ))
    
    @staticmethod
    def print_tool_call(tool_name: str, tool_args: dict):
        """
        Print tool call information.
        """
        console.print("\n")
        args_str = ""
        if tool_args:
            for key, value in tool_args.items():
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                args_str += f"  • {key}: {value}\n"
        
        console.print(Panel(
            args_str.strip() or "No arguments",
            title=f"[bold yellow]🔧 Tool Call: {tool_name}[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        ))
    
    @staticmethod
    def print_tool_result(tool_name: str, result: str):
        """
        Print tool execution result.
        """
        console.print("\n")
        if len(result) > 500:
            display_result = result[:500] + "\n... (truncated)"
        else:
            display_result = result
        
        console.print(Panel(
            display_result,
            title=f"[bold magenta]📋 Tool Result: {tool_name}[/bold magenta]",
            border_style="magenta",
            padding=(1, 2)
        ))
    
    @staticmethod
    def print_error(message: str):
        """
        Print error message.
        """
        console.print("\n")
        console.print(Panel(
            message,
            title="[bold red]❌ Error[/bold red]",
            border_style="red",
            padding=(1, 2)
        ))
    
    @staticmethod
    def print_system(message: str):
        """
        Print system message.
        """
        console.print(f"\n[bold cyan]ℹ️  {message}[/bold cyan]")


def get_tools():
    """
    Get available tools for the agent.
    """
    return [
        ReadFileTool(),
        WriteFileTool(),
        EditFileTool(),
        ListDirectoryTool()
    ]


def progress_callback(response: LLMResponse):
    """
    Callback function to handle agent responses during the loop.
    """
    if response.reasoning_content:
        OutputFormatter.print_think(response.reasoning_content)

    if response.content:
        if response.content.startswith("<think>"):
            content = response.content
            if "<think>" in content and "</think>" in content:
                think_start = content.find("<think>")
                think_end = content.find("</think>") + len("</think>")
                think_content = content[think_start:think_end]
                think_inner = think_content.replace("<think>", "").replace("</think>", "").strip()
                # if think_inner.startswith(">"):
                #     think_inner = think_inner[1:].strip()
                OutputFormatter.print_think(think_inner)
                
                remaining = content[think_end:].strip()
                if remaining:
                    OutputFormatter.print_content(remaining)
            else:
                OutputFormatter.print_think(response.content)
        else:
            OutputFormatter.print_content(response.content)
    
    if response.has_tool_calls():
        for tool_call in response.tool_calls:
            tool_name = tool_call.get("function", {}).get("name", "unknown")
            tool_args = tool_call.get("function", {}).get("arguments", {})
            if isinstance(tool_args, str):
                import json
                try:
                    tool_args = json.loads(tool_args)
                except:
                    tool_args = {}
            OutputFormatter.print_tool_call(tool_name, tool_args)


def run_agent(user_input: str, provider: DoubaoProvider, messages: list, tools: list, system_message: str = None) -> LoopResult:
    """
    Run the agent with the given input.
    """

    context = MessageBuilder(work_dir=os.getcwd())

    if system_message and len(messages) == 0:
        messages.append({
            "role": "system",
            "content": system_message
        })

    messages.append({
        "role": "user",
        "content": user_input
    })
    
    loop = ReActLoop(
        provider=provider,
        context=context,
        tools=tools,
        max_iter=20
    )
    
    result = loop.run_loop(messages, progress_callback)
    
    return result


@app.command()
def chat(
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        help="API key for the provider",
        envvar="ARK_API_KEY"
    ),
    api_url: str = typer.Option(
        "https://ark.cn-beijing.volces.com/api/v3",
        "--api-url",
        "-u",
        help="API URL for the provider"
    ),
    work_dir: str = typer.Option(
        ".",
        "--work-dir",
        "-w",
        help="Working directory"
    )
):
    """
    Start an interactive chat session with the Clarity Agent.
    """
    if not api_key:
        OutputFormatter.print_error(
            "API key is required. Please provide it via --api-key option or ARK_API_KEY environment variable."
        )
        raise typer.Exit(1)
    
    try:
        provider = DoubaoProvider(api_key=api_key, api_url=api_url)
    except Exception as e:
        OutputFormatter.print_error(f"Failed to initialize provider: {str(e)}")
        raise typer.Exit(1)
    
    tools = get_tools()
    messages = []
    
    message_builder = MessageBuilder(work_dir=work_dir)
    system_message = message_builder.build_system_message()
    
    console.clear()
    console.print(Panel(
        "[bold cyan]Welcome to Clarity Agent![/bold cyan]\n\n"
        "Type your message and press Enter to chat.\n"
        "Type [bold yellow]'exit'[/bold yellow] or [bold yellow]'quit'[/bold yellow] to exit.\n"
        "Type [bold yellow]'clear'[/bold yellow] to clear the conversation.\n"
        "Type [bold yellow]'help'[/bold yellow] for more commands.",
        title="[bold green]🤖 Clarity Agent[/bold green]",
        border_style="green",
        padding=(1, 2)
    ))
    
    OutputFormatter.print_system(f"Working directory: {os.path.abspath(work_dir)}")
    OutputFormatter.print_system(f"Available tools: {', '.join([t.name for t in tools])}")
    
    while True:
        try:
            console.print("\n[bold cyan]You:[/bold cyan] ", end="")
            user_input = input().strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit"]:
                OutputFormatter.print_system("Goodbye! 👋")
                break
            
            if user_input.lower() == "clear":
                messages = []
                console.clear()
                OutputFormatter.print_system("Conversation cleared.")
                continue
            
            if user_input.lower() == "help":
                console.print(Panel(
                    "[bold]Commands:[/bold]\n"
                    "  • [yellow]exit/quit[/yellow] - Exit the chat\n"
                    "  • [yellow]clear[/yellow] - Clear the conversation history\n"
                    "  • [yellow]help[/yellow] - Show this help message\n\n"
                    "[bold]Available Tools:[/bold]\n"
                    "  • [green]read_file[/green] - Read file contents\n"
                    "  • [green]write_file[/green] - Write content to a file\n"
                    "  • [green]edit_file[/green] - Edit a file\n"
                    "  • [green]list_directory[/green] - List directory contents",
                    title="[bold blue]📖 Help[/bold blue]",
                    border_style="blue"
                ))
                continue
            
            result = run_agent(user_input, provider, messages, tools, system_message)
            
        except KeyboardInterrupt:
            console.print("\n")
            OutputFormatter.print_system("Interrupted. Type 'exit' to quit.")
            continue
        except Exception as e:
            OutputFormatter.print_error(f"An error occurred: {str(e)}")
            continue


@app.command()
def version():
    """
    Show the version of Clarity Agent.
    """
    console.print("[bold green]Clarity Agent v0.1.0[/bold green]")


if __name__ == "__main__":
    app()
