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
DOCX-related tools for the agent system.
"""

import os
from typing import List
from agent.tool.tool_base import ToolBase, ToolParameter


class ReadDocxTool(ToolBase):
    """
    Tool for reading text content from Microsoft Word DOCX files.
    """

    @property
    def name(self) -> str:
        return "read_docx"

    @property
    def description(self) -> str:
        return "Read text content from a Microsoft Word DOCX file. Extracts all paragraphs and tables."

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type="string",
                description="The absolute path to the DOCX file to read.",
                required=True
            ),
            ToolParameter(
                name="start_paragraph",
                type="integer",
                description="The paragraph number to start reading from (0-indexed). Default is 0 (beginning).",
                required=False,
                default=0
            ),
            ToolParameter(
                name="end_paragraph",
                type="integer",
                description="The paragraph number to end reading at (0-indexed). Use -1 for all paragraphs until the end. Default is -1 (all paragraphs).",
                required=False,
                default=-1
            ),
            ToolParameter(
                name="max_chars",
                type="integer",
                description="Maximum number of characters to extract. Default is 50000 to prevent token overflow.",
                required=False,
                default=50000
            )
        ]

    def execute(self, **kwargs) -> str:
        self.validate_parameters(**kwargs)
        
        file_path = kwargs.get("file_path")
        start_paragraph = kwargs.get("start_paragraph", 0)
        end_paragraph = kwargs.get("end_paragraph", -1)
        max_chars = kwargs.get("max_chars", 50000)
        
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist."
        
        if not os.path.isfile(file_path):
            return f"Error: '{file_path}' is not a file."
        
        if not file_path.lower().endswith('.docx'):
            return f"Error: '{file_path}' is not a DOCX file."
        
        try:
            from docx import Document
            
            doc = Document(file_path)
            all_paragraphs = []
            
            for para in doc.paragraphs:
                if para.text.strip():
                    all_paragraphs.append(para.text)
            
            total_paras = len(all_paragraphs)
            
            if total_paras == 0:
                return f"Error: DOCX file '{file_path}' has no text content."
            
            start = max(0, start_paragraph)
            if end_paragraph == -1:
                end = total_paras
            else:
                end = min(end_paragraph + 1, total_paras)
            
            if start >= end:
                return f"Error: Start paragraph ({start}) is greater than or equal to end paragraph ({end})."
            
            extracted_text = []
            for idx, para in enumerate(all_paragraphs[start:end], start=start):
                extracted_text.append(para)
            
            full_text = "\n\n".join(extracted_text)
            
            if len(full_text) > max_chars:
                full_text = full_text[:max_chars] + f"\n\n[... Truncated at {max_chars} characters. Use start_paragraph and end_paragraph to read specific sections ...]"
            
            header = f"Reading DOCX: {file_path}\n"
            header += f"Paragraphs: {start} to {end-1} of {total_paras}\n"
            header += f"Characters extracted: {min(len(full_text), max_chars)}\n"
            header += "-" * 50 + "\n"
            
            return header + full_text
            
        except ImportError:
            return "Error: python-docx library is not installed. Please install it with: pip install python-docx"
        except Exception as e:
            return f"Error reading DOCX '{file_path}': {str(e)}"