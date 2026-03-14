"""
Main CLI application for Clarity Agent.
"""

import os
import sys
import typer
from typing import Optional
from pathlib import Path
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
from agent.tool import ReadFileTool, WriteFileTool, EditFileTool, ListDirectoryTool, WebScraperTool, ToolManager
from cli.config import ConfigManager, Config, ProviderConfig
from agent.provider import provider_type

app = typer.Typer(
    name="clarity",
    help="Clarity Agent - An intelligent assistant CLI tool"
)

console = Console()


class OutputFormatter:
    """
    Formatter for different types of agent output.
    """
    
    _thinking_printed = False
    
    @staticmethod
    def print_thinking():
        """
        Print 'Thinking...' indicator before model starts processing.
        """
        console.print("[bold cyan]🤔 Thinking...[/bold cyan]", end="")
        OutputFormatter._thinking_printed = True
    
    @staticmethod
    def clear_thinking():
        """
        Clear the 'Thinking...' indicator after response is received.
        """
        if OutputFormatter._thinking_printed:
            console.print("\r" + " " * 20 + "\r", end="")
            OutputFormatter._thinking_printed = False
    
    @staticmethod
    def print_think(content: str):
        """
        Print thinking content with a distinct style.
        """
        OutputFormatter.clear_thinking()
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
        OutputFormatter.clear_thinking()
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
        OutputFormatter.clear_thinking()
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
        ListDirectoryTool(),
        WebScraperTool()
    ]


def thinking_callback():
    """
    Callback function called when the model starts thinking.
    """
    OutputFormatter.print_thinking()


def progress_callback(response: LLMResponse):
    """
    Callback function to handle agent responses during the loop.
    """
    # Clear the thinking indicator first
    OutputFormatter.clear_thinking()
    
    if response.reasoning_content:
        OutputFormatter.print_think(response.reasoning_content)

    if response.content:
        if "<think" in response.content and "</think" in response.content:
            content = response.content
            # Find all occurrences of <think>...</think> tags
            import re
            think_pattern = r'<think(.*?)</think>'
            matches = re.findall(think_pattern, content, re.DOTALL)
            
            if matches:
                # Process each think block
                for match in matches:
                    think_inner = match.strip()
                    if think_inner.startswith(">"):
                        think_inner = think_inner[1:].strip()
                    OutputFormatter.print_think(think_inner)
                
                # Remove all think blocks from the content
                clean_content = re.sub(think_pattern, '', content, flags=re.DOTALL).strip()
                if clean_content:
                    OutputFormatter.print_content(clean_content)
            else:
                # No valid think tags, just print as content
                OutputFormatter.print_content(response.content)
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


def run_agent(user_input: str, provider: DoubaoProvider, messages: list, tools: list, system_message: str = None, max_iter: int = 20) -> LoopResult:
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
        max_iter=max_iter
    )
    
    result = loop.run_loop(messages, progress_callback, thinking_callback)
    
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
    api_url: Optional[str] = typer.Option(
        None,
        "--api-url",
        "-u",
        help="API URL for the provider"
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Model name to use"
    ),
    work_dir: str = typer.Option(
        ".",
        "--work-dir",
        "-w",
        help="Working directory"
    ),
    config_path: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file"
    )
):
    """
    Start an interactive chat session with the Clarity Agent.
    """
    config_manager = ConfigManager(Path(config_path) if config_path else None)
    
    loaded_config = None
    if config_manager:
        try:
            loaded_config = config_manager.load_config()
            if loaded_config:
                OutputFormatter.print_system(f"Loaded configuration from {config_manager.get_config_path()}")
        except Exception as e:
            OutputFormatter.print_error(f"Failed to load configuration: {str(e)}")
            raise typer.Exit(1)
    
    if loaded_config:
        provider_config = loaded_config.provider
        final_api_url = api_url or provider_config.api_url
        final_model = model or provider_config.model
        final_work_dir = work_dir or loaded_config.work_dir
        final_max_iter = loaded_config.max_iter
        # Use API key from config if not provided via command line
        if not api_key and provider_config.api_key:
            api_key = provider_config.api_key
    else:
        final_api_url = api_url or ""
        final_model = model or ""
        final_work_dir = work_dir
        final_max_iter = 20
    
    if not api_key:
        OutputFormatter.print_error(
            "API key is required. Please provide it via --api-key option, ARK_API_KEY environment variable, or in the configuration file."
        )
        raise typer.Exit(1)
    
    try:
        provider_type_name = loaded_config.provider.provider_type if loaded_config else "doubao"
        if provider_type_name not in provider_type:
            OutputFormatter.print_error(f"Invalid provider type in configuration: {provider_type_name}")
            OutputFormatter.print_system(f"Available provider types: {', '.join(provider_type.keys())}")
            raise typer.Exit(1)
        
        ProviderClass = provider_type[provider_type_name]
        provider = ProviderClass(api_key=api_key, api_url=final_api_url, model=final_model)
    except Exception as e:
        OutputFormatter.print_error(f"Failed to initialize provider: {str(e)}")
        raise typer.Exit(1)
    
    tools = ToolManager.get_tools_list()
    messages = []
    
    message_builder = MessageBuilder(work_dir=final_work_dir)
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
            
            result = run_agent(user_input, provider, messages, tools, system_message, final_max_iter)
            
        except KeyboardInterrupt:
            console.print("\n")
            OutputFormatter.print_system("Interrupted. Type 'exit' to quit.")
            continue
        except Exception as e:
            OutputFormatter.print_error(f"An error occurred: {str(e)}")
            continue


@app.command()
def config(
    action: str = typer.Argument(..., help="Action to perform: 'create', 'show', or 'edit'"),
    config_path: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file"
    ),
    provider_type_arg: Optional[str] = typer.Option(
        None,
        "--provider-type",
        "-p",
        help="Provider type (e.g., 'doubao')"
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Model name"
    ),
    api_url: Optional[str] = typer.Option(
        None,
        "--api-url",
        "-u",
        help="API URL"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        help="API key (will be saved in plain text)"
    ),
    work_dir: Optional[str] = typer.Option(
        None,
        "--work-dir",
        "-w",
        help="Working directory"
    ),
    max_iter: Optional[int] = typer.Option(
        None,
        "--max-iter",
        help="Maximum iterations"
    )
):
    """
    Manage configuration for Clarity Agent.
    
    Actions:
    - create: Create a new configuration file
    - show: Show current configuration
    - edit: Edit existing configuration
    """
    config_manager = ConfigManager(Path(config_path) if config_path else None)
    
    if action == "create":
        final_provider_type = provider_type_arg or ""
        if final_provider_type not in provider_type:
            OutputFormatter.print_error(f"Invalid provider type: {final_provider_type}")
            OutputFormatter.print_system(f"Available provider types: {', '.join(provider_type.keys())}")
            raise typer.Exit(1)
        
        provider_config = ProviderConfig(
            provider_type=final_provider_type,
            model=model or "",
            api_url=api_url or "",
            api_key=api_key
        )
        
        config = Config(
            provider=provider_config,
            work_dir=work_dir or ".",
            max_iter=max_iter or 20
        )
        
        try:
            config_manager = config_manager or ConfigManager()
            config_manager.save_config(config)
            OutputFormatter.print_system(f"Configuration created at {config_manager.get_config_path()}")
            console.print(Panel(
                f"Provider Type: {config.provider.provider_type}\n"
                f"Model: {config.provider.model}\n"
                f"API URL: {config.provider.api_url}\n"
                f"Work Directory: {config.work_dir}\n"
                f"Max Iterations: {config.max_iter}",
                title="[bold green]✅ Configuration Created[/bold green]",
                border_style="green"
            ))
        except Exception as e:
            OutputFormatter.print_error(f"Failed to create configuration: {str(e)}")
            raise typer.Exit(1)
    
    elif action == "show":
        if not config_manager:
            config_manager = ConfigManager()
        
        try:
            config = config_manager.load_config()
            if config:
                # Mask API key for privacy
                api_key_display = "[hidden]" if config.provider.api_key else "[not set]"
                if config.provider.api_key and len(config.provider.api_key) > 8:
                    api_key_display = config.provider.api_key[:4] + "****" + config.provider.api_key[-4:]
                
                console.print(Panel(
                    f"Provider Type: {config.provider.provider_type}\n"
                    f"Model: {config.provider.model}\n"
                    f"API URL: {config.provider.api_url}\n"
                    f"API Key: {api_key_display}\n"
                    f"Work Directory: {config.work_dir}\n"
                    f"Max Iterations: {config.max_iter}",
                    title="[bold blue]📋 Current Configuration[/bold blue]",
                    border_style="blue"
                ))
            else:
                OutputFormatter.print_error(f"No configuration found at {config_manager.get_config_path()}")
                OutputFormatter.print_system("Use 'config create' to create a new configuration.")
        except Exception as e:
            OutputFormatter.print_error(f"Failed to load configuration: {str(e)}")
            raise typer.Exit(1)
    
    elif action == "edit":
        if not config_manager:
            config_manager = ConfigManager()
        
        try:
            config = config_manager.load_config()
            if not config:
                OutputFormatter.print_error(f"No configuration found at {config_manager.get_config_path()}")
                OutputFormatter.print_system("Use 'config create' to create a new configuration.")
                raise typer.Exit(1)
            
            if provider_type_arg:
                if provider_type_arg not in provider_type:
                    OutputFormatter.print_error(f"Invalid provider type: {provider_type_arg}")
                    OutputFormatter.print_system(f"Available provider types: {', '.join(provider_type.keys())}")
                    raise typer.Exit(1)
                config.provider.provider_type = provider_type_arg
            if model:
                config.provider.model = model
            if api_url:
                config.provider.api_url = api_url
            if api_key is not None:
                config.provider.api_key = api_key
            if work_dir:
                config.work_dir = work_dir
            if max_iter:
                config.max_iter = max_iter
            
            config_manager.save_config(config)
            OutputFormatter.print_system(f"Configuration updated at {config_manager.get_config_path()}")
            console.print(Panel(
                f"Provider Type: {config.provider.provider_type}\n"
                f"Model: {config.provider.model}\n"
                f"API URL: {config.provider.api_url}\n"
                f"Work Directory: {config.work_dir}\n"
                f"Max Iterations: {config.max_iter}",
                title="[bold green]✅ Configuration Updated[/bold green]",
                border_style="green"
            ))
        except Exception as e:
            OutputFormatter.print_error(f"Failed to update configuration: {str(e)}")
            raise typer.Exit(1)
    
    else:
        OutputFormatter.print_error(f"Unknown action: {action}")
        OutputFormatter.print_system("Available actions: create, show, edit")
        raise typer.Exit(1)


@app.command()
def version():
    """
    Show the version of Clarity Agent.
    """
    console.print("[bold green]Clarity Agent v0.1.0[/bold green]")


if __name__ == "__main__":
    app()
