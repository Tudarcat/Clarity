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
File-related tools for the agent system.
"""

import os
from typing import List
from agent.tool.tool_base import ToolBase, ToolParameter


class ReadFileTool(ToolBase):
    """
    Tool for reading file contents.
    """

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the contents of a file from the filesystem."

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type="string",
                description="The absolute path to the file to read.",
                required=True
            ),
            ToolParameter(
                name="offset",
                type="integer",
                description="The line number to start reading from (1-indexed). Default is 1.",
                required=False,
                default=1
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="The maximum number of lines to read. Default is 2000.",
                required=False,
                default=2000
            )
        ]

    def execute(self, **kwargs) -> str:
        self.validate_parameters(**kwargs)
        
        file_path = kwargs.get("file_path")
        offset = kwargs.get("offset", 1)
        limit = kwargs.get("limit", 2000)
        
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist."
        
        if not os.path.isfile(file_path):
            return f"Error: '{file_path}' is not a file."
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            start = max(0, offset - 1)
            end = min(len(lines), start + limit)
            
            result_lines = []
            for i in range(start, end):
                result_lines.append(f"{i + 1:6d}→{lines[i].rstrip()}")
            
            if not result_lines:
                return f"File '{file_path}' is empty or offset is beyond file length."
            
            header = f"Reading file: {file_path}\n"
            header += f"Lines {start + 1}-{end} of {len(lines)}\n"
            header += "-" * 50 + "\n"
            
            return header + "\n".join(result_lines)
        except Exception as e:
            return f"Error reading file '{file_path}': {str(e)}"


class WriteFileTool(ToolBase):
    """
    Tool for writing content to a file.
    """

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "Write content to a file. This will overwrite the file if it exists."

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type="string",
                description="The absolute path to the file to write.",
                required=True
            ),
            ToolParameter(
                name="content",
                type="string",
                description="The content to write to the file.",
                required=True
            )
        ]

    def execute(self, **kwargs) -> str:
        self.validate_parameters(**kwargs)
        
        file_path = kwargs.get("file_path")
        content = kwargs.get("content")
        
        try:
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            return f"Successfully wrote {len(content)} characters to '{file_path}'."
        except Exception as e:
            return f"Error writing to file '{file_path}': {str(e)}"


class EditFileTool(ToolBase):
    """
    Tool for editing a file by replacing specific content.
    """

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return "Edit a file by replacing a specific chunk of content with new content."

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type="string",
                description="The absolute path to the file to edit.",
                required=True
            ),
            ToolParameter(
                name="old_content",
                type="string",
                description="The content to search for and replace. This must be an exact match.",
                required=True
            ),
            ToolParameter(
                name="new_content",
                type="string",
                description="The new content to replace the old content with.",
                required=True
            )
        ]

    def execute(self, **kwargs) -> str:
        self.validate_parameters(**kwargs)
        
        file_path = kwargs.get("file_path")
        old_content = kwargs.get("old_content")
        new_content = kwargs.get("new_content")
        
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist."
        
        if not os.path.isfile(file_path):
            return f"Error: '{file_path}' is not a file."
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if old_content not in content:
                return f"Error: The specified old_content was not found in '{file_path}'."
            
            count = content.count(old_content)
            if count > 1:
                return f"Error: The old_content appears {count} times in the file. Please provide more context to make it unique."
            
            new_file_content = content.replace(old_content, new_content, 1)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_file_content)
            
            return f"Successfully edited '{file_path}'. Replaced 1 occurrence."
        except Exception as e:
            return f"Error editing file '{file_path}': {str(e)}"


class ListDirectoryTool(ToolBase):
    """
    Tool for listing the contents of a directory.
    """

    @property
    def name(self) -> str:
        return "list_directory"

    @property
    def description(self) -> str:
        return "List the contents of a directory, showing files and subdirectories."

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="directory_path",
                type="string",
                description="The absolute path to the directory to list.",
                required=True
            ),
            ToolParameter(
                name="recursive",
                type="boolean",
                description="Whether to list contents recursively. Default is false.",
                required=False,
                default=False
            )
        ]

    def execute(self, **kwargs) -> str:
        self.validate_parameters(**kwargs)
        
        directory_path = kwargs.get("directory_path")
        recursive = kwargs.get("recursive", False)
        
        if not os.path.exists(directory_path):
            return f"Error: Directory '{directory_path}' does not exist."
        
        if not os.path.isdir(directory_path):
            return f"Error: '{directory_path}' is not a directory."
        
        try:
            result_lines = []
            result_lines.append(f"Contents of '{directory_path}':")
            result_lines.append("-" * 50)
            
            if recursive:
                for root, dirs, files in os.walk(directory_path):
                    level = root.replace(directory_path, "").count(os.sep)
                    indent = " " * 2 * level
                    
                    rel_root = os.path.relpath(root, directory_path)
                    if rel_root == ".":
                        result_lines.append(f"{indent}[{os.path.basename(root)}/]")
                    else:
                        result_lines.append(f"{indent}[{rel_root}/]")
                    
                    sub_indent = " " * 2 * (level + 1)
                    for file in sorted(files):
                        file_path = os.path.join(root, file)
                        size = os.path.getsize(file_path)
                        result_lines.append(f"{sub_indent}{file} ({size} bytes)")
                    
                    for dir_name in sorted(dirs):
                        pass
            else:
                entries = sorted(os.listdir(directory_path))
                
                for entry in entries:
                    entry_path = os.path.join(directory_path, entry)
                    if os.path.isdir(entry_path):
                        result_lines.append(f"[{entry}/]")
                    else:
                        size = os.path.getsize(entry_path)
                        result_lines.append(f"{entry} ({size} bytes)")
            
            return "\n".join(result_lines)
        except Exception as e:
            return f"Error listing directory '{directory_path}': {str(e)}"
