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
Main CLI application for Clarity Agent.
"""

import os
import sys
import asyncio
import typer
from typing import Optional
from pathlib import Path
from rich.panel import Panel
from rich.console import Console
from rich.markdown import Markdown
from rich import print as rprint

# Try to import readline or use a fallback for Windows
try:
    import readline
except ImportError:
    # Windows fallback
    try:
        import pyreadline3 as readline
    except ImportError:
        readline = None

from agent.provider.provider_base import LLMResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.provider import CustomProvider
from agent.core.loop import ReActLoop, LoopResult
from agent.core.message import MessageBuilder
from agent.tool import ReadFileTool, WriteFileTool, EditFileTool, ListDirectoryTool, WebScraperTool, ToolManager
from cli.config import ConfigManager, Config, ProviderConfig
from cli.streaming import create_streaming_callback
from agent.provider import provider_type
import platform
import subprocess

app = typer.Typer(
    name="clarity",
    help="Clarity Agent - An intelligent assistant CLI tool"
)

console = Console()


def open_file_in_editor(file_path: Path):
    """
    Open a file in the default text editor.
    
    :param file_path: Path to the file to open.
    """
    try:
        if platform.system() == 'Windows':
            os.startfile(str(file_path))
        elif platform.system() == 'Darwin':
            subprocess.run(['open', str(file_path)], check=True)
        else:
            subprocess.run(['xdg-open', str(file_path)], check=True)
        OutputFormatter.print_system(f"Opened config file in editor: {file_path}")
    except Exception as e:
        OutputFormatter.print_error(f"Failed to open file in editor: {str(e)}")
        OutputFormatter.print_system(f"You can manually edit the file at: {file_path}")


# Command completion for / commands
COMMANDS = [
    '/help',
    '/exit',
    '/quit',
    '/clear',
    '/config',
    '/version'
]

def completer(text, state):
    """Command completion function for readline."""
    if not text:
        return COMMANDS[state] if state < len(COMMANDS) else None
    
    matches = [cmd for cmd in COMMANDS if cmd.startswith(text)]
    return matches[state] if state < len(matches) else None

# Set up readline for command completion if available
if readline:
    readline.set_completer(completer)
    if hasattr(readline, 'parse_and_bind'):
        readline.parse_and_bind('tab: complete')


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
        #console.print("[bold cyan]🤔 Thinking...[/bold cyan]", end="")
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
        console.print(f"\n[italic]{content}[/italic]")
    
    @staticmethod
    def print_content(content: str):
        """
        Print regular content.
        """
        OutputFormatter.clear_thinking()
        console.print(f"\n[bold]●[/bold]")
        console.print(Markdown(content))
    
    @staticmethod
    def print_tool_call(tool_name: str, tool_args: dict):
        """
        Print tool call information in tree-like format.
        """
        OutputFormatter.clear_thinking()
        
        if tool_name == "update_task":
            console.print("\n[bold cyan]📋 Task Plan Updated[/bold cyan]")
            console.print("-" * console.width, style="cyan")
            
            if isinstance(tool_args, dict):
                task = tool_args.get("task", "")
                steps = tool_args.get("steps", [])
                success_criteria = tool_args.get("success_criteria", "")
            else:
                console.print(f"[bold]Raw Arguments:[/bold] {tool_args}")
                console.print("-" * console.width, style="cyan")
                return
            
            console.print(f"[bold]Task:[/bold] {task}")
            console.print(f"[bold]Success Criteria:[/bold] {success_criteria}")
            console.print("")
            
            console.print("[bold]Steps:[/bold]")
            if not isinstance(steps, list):
                console.print(f"  [red]Error: steps is not a list[/red]")
            else:
                for i, step in enumerate(steps, 1):
                    if isinstance(step, str):
                        console.print(f"  {i}. [yellow][PENDING][/yellow] {step}")
                        continue
                    if not isinstance(step, dict):
                        console.print(f"  {i}. [red]Error: step is not a dict - {type(step)}[/red]")
                        continue
                    
                    status = step.get("status", "pending")
                    description = step.get("description", "")
                    tool = step.get("tool", "")
                    
                    status_colors = {
                        "completed": "green",
                        "pending": "yellow",
                        "in_progress": "blue",
                        "failed": "red",
                        "skipped": "gray"
                    }
                    status_color = status_colors.get(status, "yellow")
                    
                    step_line = f"  {i}. [{status_color}][{status.upper()}][/{status_color}] {description}"
                    if tool:
                        step_line += f" [dim](Tool: {tool})[/dim]"
                    console.print(step_line)
            
            console.print("-" * console.width, style="cyan")
        else:
            console.print(f"\n[bold]● {tool_name}[/bold]")
            
            if tool_args:
                items = list(tool_args.items()) if isinstance(tool_args, dict) else []
                for i, (key, value) in enumerate(items):
                    is_last = i == len(items) - 1
                    branch = "└──" if is_last else "├──"
                    
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    console.print(f"  {branch} [dim]{key}:[/dim] {value}")
    
    @staticmethod
    def print_tool_result(tool_name: str, result: str):
        """
        Print tool execution result.
        """
        if len(result) > 300:
            display_result = result[:300] + "..."
        else:
            display_result = result
        console.print(f"[dim]→ {display_result}[/dim]")
    
    @staticmethod
    def print_error(message: str):
        """
        Print error message.
        """
        console.print(f"\n[bold red]❌ Error:[/bold red] {message}")
    
    @staticmethod
    def print_system(message: str):
        """
        Print system message.
        """
        console.print(f"\n[cyan]ℹ️ {message}[/cyan]")
    
    @staticmethod
    def print_analysis(analysis):
        """
        Print task complexity analysis.
        """
        strategy_color = "green" if analysis.recommended_strategy == LoopStrategy.REACT else "yellow"
        strategy_icon = "⚡" if analysis.recommended_strategy == LoopStrategy.REACT else "📋"
        
        console.print(f"\n[bold]🔍 Analysis:[/bold] [{strategy_color}]{strategy_icon} {analysis.recommended_strategy.value.upper()}[/{strategy_color}] | "
                      f"Steps: {analysis.estimated_steps} | "
                      f"Confidence: {analysis.confidence:.0%}")
    
    @staticmethod
    def print_plan(plan):
        """
        Print execution plan using simple list format.
        """
        console.print(f"\n[yellow]📋 Plan:[/yellow] [bold]{plan.task}[/bold]")
        
        for step in plan.steps:
            status_icons = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
                "failed": "❌",
                "skipped": "⏭️"
            }
            status = step.status.value if hasattr(step.status, 'value') else str(step.status)
            icon = status_icons.get(status, "⏳")
            tool_str = f" [dim]({step.tool})[/dim]" if step.tool else ""
            console.print(f"  {icon} {step.id}. {step.description}{tool_str}")
        
        completed, total = plan.get_progress()
        console.print(f"[dim]   Progress: {completed}/{total}[/dim]")


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


def progress_callback(response: LLMResponse, stream_cb=None):
    """
    Callback function to handle agent responses during the loop.
    """
    OutputFormatter.clear_thinking()

    if response.reasoning_content:
        OutputFormatter.print_think(response.reasoning_content)

    if response.content:
        if "<think" in response.content and "</think" in response.content:
            import re
            think_pattern = r'<think(.*?)</think>'
            matches = re.findall(think_pattern, response.content, re.DOTALL)

            if matches:
                for match in matches:
                    think_inner = match.strip()
                    if think_inner.startswith(">"):
                        think_inner = think_inner[1:].strip()
                    OutputFormatter.print_think(think_inner)

                clean_content = re.sub(think_pattern, '', response.content, flags=re.DOTALL).strip()
                if clean_content:
                    OutputFormatter.print_content(clean_content)
            else:
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


def run_agent(
    user_input: str,
    provider: CustomProvider,
    messages: list,
    tools: list,
    system_message: str = None,
    max_iter: int = 20,
    streaming: bool = False
) -> LoopResult:
    """
    Run the agent with the given input using ReAct loop.

    :param streaming: Whether to enable streaming mode for real-time output.
    """
    context = MessageBuilder(work_dir=os.getcwd())

    OutputFormatter.print_system("Processing task...")

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

    stream_cb = create_streaming_callback(console, streaming)
    stream_cb.start()

    try:
        result = loop.run_loop(
            messages,
            lambda r: progress_callback(r, stream_cb),
            thinking_callback,
            streaming=streaming,
            stream_callback=stream_cb
        )
    finally:
        stream_cb.stop()

    return result


async def run_agent_async(
    user_input: str,
    provider: CustomProvider,
    messages: list,
    tools: list,
    system_message: str = None,
    max_iter: int = 20,
    streaming: bool = False
) -> LoopResult:
    """
    Async version of run_agent. Run the agent with the given input using async ReAct loop.

    :param streaming: Whether to enable streaming mode for real-time output.
    """
    context = MessageBuilder(work_dir=os.getcwd())

    OutputFormatter.print_system("Processing task...")

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

    stream_cb = create_streaming_callback(console, streaming)
    stream_cb.start()

    try:
        result = await loop.arun_loop(
            messages,
            lambda r: progress_callback(r, stream_cb),
            thinking_callback,
            streaming=streaming,
            stream_callback=stream_cb
        )
    finally:
        stream_cb.stop()

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
        final_streaming = loaded_config.streaming
        if not api_key and provider_config.api_key:
            api_key = provider_config.api_key
    else:
        final_api_url = api_url or ""
        final_model = model or ""
        final_work_dir = work_dir
        final_max_iter = 20
        final_streaming = True
    
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
    token_usage: int = 0
    
    message_builder = MessageBuilder(work_dir=final_work_dir)
    system_message = message_builder.build_system_message()
    
    console.clear()
    console.print(Panel(
        "[bold cyan]Welcome to Clarity Agent![/bold cyan]\n\n"
        "Type your message and press Enter to chat.\n"
        "Type [bold yellow]/exit[/bold yellow] or [bold yellow]/quit[/bold yellow] to exit.\n"
        "Type [bold yellow]/clear[/bold yellow] to clear the conversation.\n"
        "Type [bold yellow]/help[/bold yellow] for more commands.\n"
        "Press [bold yellow]Tab[/bold yellow] for command suggestions.",
        title="[bold green]🤖 Clarity Agent[/bold green]",
        border_style="green",
        padding=(1, 2)
    ))
    
    OutputFormatter.print_system(f"Working directory: {os.path.abspath(work_dir)}")
    OutputFormatter.print_system(f"Available tools: {', '.join([t.name for t in tools])}")
    
    while True:
        try:
            # Print Claude Code style input box
            console.print("─" * console.width, style="cyan")
            console.print("[bold cyan]>[/bold cyan] ", end="")
            user_input = input().strip()
            console.print("─" * console.width, style="cyan")
            
            if not user_input:
                continue
            
            # Handle commands with / prefix
            if user_input.startswith('/'):
                # Split into command and arguments
                parts = user_input[1:].split(' ', 1)
                command = parts[0].lower()
                args = parts[1].strip() if len(parts) > 1 else ''
                
                if command in ["exit", "quit"]:
                    OutputFormatter.print_system("Goodbye! 👋")
                    break
                
                if command == "clear":
                    messages = []
                    console.clear()
                    OutputFormatter.print_system("Conversation cleared.")
                    continue
                
                if command == "help":
                    console.print(Panel(
                        "[bold]Commands:[/bold]\n"
                        "  • [yellow]/exit[/yellow] - Exit the chat\n"
                        "  • [yellow]/quit[/yellow] - Exit the chat\n"
                        "  • [yellow]/clear[/yellow] - Clear the conversation history\n"
                        "  • [yellow]/help[/yellow] - Show this help message\n"
                        "  • [yellow]/config[/yellow] - Show configuration\n"
                        "  • [yellow]/version[/yellow] - Show version\n\n"
                        "[bold]Config Tool Tips:[/bold]\n"
                        "  • [blue]config create[/blue] - Creates config and opens editor\n"
                        "  • [blue]config create -n[/blue] - Creates config without opening editor\n"
                        "  • [blue]config edit[/blue] - Opens config file in editor\n"
                        "  • [blue]config edit --model xxx[/blue] - Edits via command line\n\n"
                        "[bold]Available Tools:[/bold]\n"
                        "  • [green]read_file[/green] - Read file contents\n"
                        "  • [green]write_file[/green] - Write content to a file\n"
                        "  • [green]edit_file[/green] - Edit a file\n"
                        "  • [green]list_directory[/green] - List directory contents\n"
                        "  • [green]read_pdf[/green] - Read text from PDF file\n"
                        "  • [green]read_docx[/green] - Read text from DOCX file\n"
                        "  • [green]exec_shell[/green] - Execute shell commands\n", 
                        title="[bold blue]📖 Help[/bold blue]",
                        border_style="blue"
                    ))
                    continue
                
                if command == "config":
                    # Show configuration
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
                    continue
                
                if command == "version":
                    console.print("[bold green]Clarity Agent v0.1.0[/bold green]")
                    continue
                
                # Unknown command
                OutputFormatter.print_error(f"Unknown command: {user_input}")
                OutputFormatter.print_system("Type /help for a list of available commands.")
                continue
            
            # check if token usage exceeds max tokens
            if token_usage > provider.get_max_tokens() * 0.80:
                # compress
                from agent.summary import Summary
                summary = Summary(provider)
                # clear messages
                messages.clear()
                messages = [
                    {
                    "role": "system",
                    "content": system_message
                    }
                ]
                messages += summary.summarize(messages)
                # OutputFormatter.print_system(str(messages))
                token_usage = 0
                OutputFormatter.print_system("Conversation compressed.")

            # Handle regular input
            result = run_agent(user_input, provider, messages, tools, system_message, final_max_iter, streaming=final_streaming)
            
            # count token usage
            if result.token_usage:
                token_usage = result.token_usage["total_tokens"]
            
        except KeyboardInterrupt:
            console.print("\n")
            OutputFormatter.print_system("Interrupted. Type /exit to quit.")
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
    no_open: bool = typer.Option(
        False,
        "--no-open",
        "-n",
        help="Don't open config file in editor after creating"
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
            
            if not no_open:
                open_file_in_editor(config_manager.get_config_path())
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
            
            # If no parameters are provided, just open the editor
            has_any_param = any([
                provider_type_arg,
                model,
                api_url,
                api_key is not None,
                work_dir,
                max_iter
            ])
            
            if not has_any_param:
                OutputFormatter.print_system(f"Opening config file in editor: {config_manager.get_config_path()}")
                open_file_in_editor(config_manager.get_config_path())
                return
            
            # Otherwise, update via command line
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
