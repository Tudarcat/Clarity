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
This module provides the base class for tools in the agent system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass, field
import asyncio


@dataclass
class ToolParameter:
    """
    Represents a parameter for a tool.
    """
    name: str
    type: str
    description: str
    required: bool = True
    enum: List[str] | None = None
    default: Any = None


@dataclass
class ToolSchema:
    """
    Represents the schema for a tool, including its name, description, and parameters.
    """
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the tool schema to a dictionary format compatible with OpenAI function calling.
        
        :return: A dictionary representing the tool schema.
        """
        properties = {}
        required = []
        
        for param in self.parameters:
            prop = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                prop["enum"] = param.enum
            properties[param.name] = prop
            
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }


class ToolBase(ABC):
    """
    Base class for all tools in the agent system.
    All tools must inherit from this class and implement the required methods.
    """

    def __init__(self):
        self._schema: ToolSchema | None = None

    @property
    @abstractmethod
    def name(self) -> str:
        """
        The name of the tool.
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        A description of what the tool does.
        """
        pass

    @property
    def parameters(self) -> List[ToolParameter]:
        """
        The parameters for the tool.
        Override this property to define tool-specific parameters.
        """
        return []

    def get_schema(self) -> ToolSchema:
        """
        Get the schema for this tool.
        
        :return: A ToolSchema object representing the tool's schema.
        """
        if self._schema is None:
            self._schema = ToolSchema(
                name=self.name,
                description=self.description,
                parameters=self.parameters
            )
        return self._schema

    def to_openai_tool(self) -> Dict[str, Any]:
        """
        Convert the tool to OpenAI function calling format.
        
        :return: A dictionary representing the tool in OpenAI format.
        """
        return self.get_schema().to_dict()

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """
        Execute the tool with the given parameters.

        :param kwargs: The parameters for the tool.
        :return: The result of the tool execution as a string.
        """
        pass

    async def aexecute(self, **kwargs) -> str:
        """
        Async version of execute. Default implementation wraps execute() in asyncio.to_thread().
        Override this method in subclasses for native async implementation.

        :param kwargs: The parameters for the tool.
        :return: The result of the tool execution as a string.
        """
        return await asyncio.to_thread(self.execute, **kwargs)

    def validate_parameters(self, **kwargs) -> bool:
        """
        Validate the provided parameters against the tool's schema.
        
        :param kwargs: The parameters to validate.
        :return: True if the parameters are valid, False otherwise.
        """
        param_names = {p.name for p in self.parameters}
        required_params = {p.name for p in self.parameters if p.required}
        
        provided_params = set(kwargs.keys())
        
        if not required_params.issubset(provided_params):
            missing = required_params - provided_params
            raise ValueError(f"Missing required parameters: {missing}")
        
        if not provided_params.issubset(param_names):
            unknown = provided_params - param_names
            raise ValueError(f"Unknown parameters: {unknown}")
        
        return True
