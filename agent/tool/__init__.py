"""
This module provides the tool system for the agent.
"""
from agent.tool.tool_base import ToolBase, ToolParameter, ToolSchema
from agent.tool.file_tools import ReadFileTool, WriteFileTool, EditFileTool, ListDirectoryTool
from agent.tool.web_tools import WebScraperTool, PaperSearchTool
from agent.tool.tool_manager import ToolManager

__all__ = [
    "ToolBase",
    "ToolParameter",
    "ToolSchema",
    "ReadFileTool",
    "WriteFileTool",
    "EditFileTool",
    "ListDirectoryTool",
    "WebScraperTool",
    "PaperSearchTool",
    "ToolManager"
]
