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
Shell execution tools for the agent system.
"""

import subprocess
import sys
import os
from typing import List
from agent.tool.tool_base import ToolBase, ToolParameter


class ShellExecTool(ToolBase):
    """
    Tool for executing shell commands and capturing output.
    """

    @property
    def name(self) -> str:
        return "exec_shell"

    @property
    def description(self) -> str:
        return "Execute a shell command and return stdout, stderr, and exit code. Use with caution - only execute trusted commands."

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="command",
                type="string",
                description="The shell command to execute. Can be a single command or a chain of commands.",
                required=True
            ),
            ToolParameter(
                name="cwd",
                type="string",
                description="Working directory for command execution. Defaults to current working directory.",
                required=False
            ),
            ToolParameter(
                name="timeout",
                type="integer",
                description="Timeout in seconds for command execution. Default is 60 seconds.",
                required=False,
                default=60
            ),
            ToolParameter(
                name="max_output_chars",
                type="integer",
                description="Maximum number of characters to return for stdout and stderr. Default is 50000 to prevent token overflow.",
                required=False,
                default=50000
            )
        ]

    def execute(self, **kwargs) -> str:
        self.validate_parameters(**kwargs)
        
        command = kwargs.get("command")
        cwd = kwargs.get("cwd")
        timeout = kwargs.get("timeout", 60)
        max_output_chars = kwargs.get("max_output_chars", 50000)
        
        if not command or not command.strip():
            return "Error: No command provided."
        
        if cwd and not os.path.exists(cwd):
            return f"Error: Working directory '{cwd}' does not exist."
        
        if cwd and not os.path.isdir(cwd):
            return f"Error: '{cwd}' is not a directory."
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            stdout = result.stdout
            stderr = result.stderr
            exit_code = result.returncode
            
            output_parts = []
            
            output_parts.append("=" * 60)
            output_parts.append(f"Command: {command}")
            if cwd:
                output_parts.append(f"Working Directory: {cwd}")
            output_parts.append(f"Exit Code: {exit_code}")
            output_parts.append("=" * 60)
            
            if stdout:
                if len(stdout) > max_output_chars:
                    truncated = stdout[:max_output_chars]
                    output_parts.append("\n[STDOUT - Truncated]")
                    output_parts.append(truncated)
                    output_parts.append(f"\n[... Truncated at {max_output_chars} characters ...]")
                else:
                    output_parts.append("\n[STDOUT]")
                    output_parts.append(stdout)
            
            if stderr:
                if len(stderr) > max_output_chars:
                    truncated = stderr[:max_output_chars]
                    output_parts.append("\n[STDERR - Truncated]")
                    output_parts.append(truncated)
                    output_parts.append(f"\n[... Truncated at {max_output_chars} characters ...]")
                else:
                    output_parts.append("\n[STDERR]")
                    output_parts.append(stderr)
            
            return "\n".join(output_parts)
            
        except subprocess.TimeoutExpired:
            output_parts = []
            output_parts.append("=" * 60)
            output_parts.append(f"Command: {command}")
            if cwd:
                output_parts.append(f"Working Directory: {cwd}")
            output_parts.append(f"Error: Command timed out after {timeout} seconds.")
            output_parts.append("=" * 60)
            return "\n".join(output_parts)
        except Exception as e:
            return f"Error executing command '{command}': {str(e)}"