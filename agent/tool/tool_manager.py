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
This module provides the tool manager for loading and registering tools.
"""

from typing import List

from agent.tool.web_tools import PaperSearchTool, WebScraperTool
from agent.tool.tool_base import ToolBase
from agent.tool.file_tools import EditFileTool
from agent.tool.file_tools import ReadFileTool
from agent.tool.file_tools import WriteFileTool
from agent.tool.file_tools import ListDirectoryTool
from agent.tool.task_tools import UpdateTaskTool
from agent.tool.pdf_tools import ReadPDFTool
from agent.tool.knowledge_repo import KnowledgeRepo

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
        UpdateTaskTool(),
        ReadPDFTool(),
        KnowledgeRepo()
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
