from typing import List

from agent.tool.web_tools import PaperSearchTool, WebScraperTool
from agent.tool.tool_base import ToolBase
from agent.tool.file_tools import EditFileTool
from agent.tool.file_tools import ReadFileTool
from agent.tool.file_tools import WriteFileTool
from agent.tool.file_tools import ListDirectoryTool

class ToolManager:
    """
    Manager for loading and registering tools.
    """

    tools_list = [
        WebScraperTool(),
        EditFileTool(),
        ReadFileTool(),
        WriteFileTool(),
        ListDirectoryTool(),
        PaperSearchTool(),
    ]
    tools_dict = {tool.name: tool for tool in tools_list}
    
    def __init__(self):
        pass

    @staticmethod
    def get_tools_list() -> List[ToolBase]:
        """
        Get the list of registered tools.
        
        :return: List of ToolBase instances.
        """
        return ToolManager.tools_list
    
    @staticmethod
    def get_tool(tool_name: str) -> ToolBase:   
        """
        Get a tool by name.
        
        :param tool_name: Name of the tool to retrieve.
        :return: ToolBase instance if found, None otherwise.
        """
        return ToolManager.tools_dict.get(tool_name)
