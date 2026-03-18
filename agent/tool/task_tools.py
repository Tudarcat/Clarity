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
This module provides tools for task management and planning.
"""

from typing import List, Dict, Any
from agent.tool.tool_base import ToolBase, ToolParameter


class UpdateTaskTool(ToolBase):
    """
    Tool for updating task plans and status.
    """

    @property
    def name(self) -> str:
        return "update_task"

    @property
    def description(self) -> str:
        return "Update task plan and status. Use this tool to plan or modify tasks when tasks are complex or require multiple steps. Dont use this tool for simple tasks. Dont miss the description of the task."

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="task",
                type="string",
                description="The overall task description (must)",
                required=True
            ),
            ToolParameter(
                name="steps",
                type="array",
                description="List of task steps",
                required=True
            ),
            ToolParameter(
                name="success_criteria",
                type="string",
                description="Criteria for task completion",
                required=True
            )
        ]

    def execute(self, **kwargs) -> str:
        """
        Execute the task update tool.
        
        :param kwargs: The parameters for the tool.
        :return: The result of the tool execution as a string.
        """
        task = kwargs.get("task", "")
        steps = kwargs.get("steps", [])
        success_criteria = kwargs.get("success_criteria", "")
        
        # Validate steps format
        for i, step in enumerate(steps, 1):
            if not isinstance(step, dict):
                return f"Error: Step {i} must be a dictionary"
            if "description" not in step:
                return f"Error: Step {i} missing 'description' field"
            if "status" not in step:
                return f"Error: Step {i} missing 'status' field"
        
        # Generate response
        response = f"Task updated successfully!\n\n"
        response += f"Task: {task}\n"
        response += f"Success Criteria: {success_criteria}\n\n"
        response += "Steps:\n"
        
        for i, step in enumerate(steps, 1):
            status = step.get("status", "pending")
            description = step.get("description", "")
            tool = step.get("tool", "")
            
            response += f"  {i}. [{status.upper()}] {description}"
            if tool:
                response += f" (Tool: {tool})"
            response += "\n"
        
        return response