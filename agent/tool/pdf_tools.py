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
PDF-related tools for the agent system.
"""

import os
from typing import List
from agent.tool.tool_base import ToolBase, ToolParameter


class ReadPDFTool(ToolBase):
    """
    Tool for reading text content from PDF files.
    """

    @property
    def name(self) -> str:
        return "read_pdf"

    @property
    def description(self) -> str:
        return "Read text content from a PDF file. Extracts text from specified pages or the entire document."

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type="string",
                description="The absolute path to the PDF file to read.",
                required=True
            ),
            ToolParameter(
                name="start_page",
                type="integer",
                description="The page number to start reading from (1-indexed). Default is 1.",
                required=False,
                default=1
            ),
            ToolParameter(
                name="end_page",
                type="integer",
                description="The page number to end reading at (1-indexed). Use -1 for all pages until the end. Default is -1 (all pages).",
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
        start_page = kwargs.get("start_page", 1)
        end_page = kwargs.get("end_page", -1)
        max_chars = kwargs.get("max_chars", 50000)
        
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist."
        
        if not os.path.isfile(file_path):
            return f"Error: '{file_path}' is not a file."
        
        if not file_path.lower().endswith('.pdf'):
            return f"Error: '{file_path}' is not a PDF file."
        
        try:
            from PyPDF2 import PdfReader
            
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            
            if total_pages == 0:
                return f"Error: PDF file '{file_path}' has no pages."
            
            start = max(1, start_page)
            if end_page == -1:
                end = total_pages
            else:
                end = min(end_page, total_pages)
            
            if start > end:
                return f"Error: Start page ({start}) is greater than end page ({end})."
            
            extracted_text = []
            for page_num in range(start - 1, end):
                page = reader.pages[page_num]
                text = page.extract_text()
                if text:
                    extracted_text.append(f"--- Page {page_num + 1} ---\n{text}")
            
            full_text = "\n\n".join(extracted_text)
            
            if len(full_text) > max_chars:
                full_text = full_text[:max_chars] + f"\n\n[... Truncated at {max_chars} characters. Use start_page and end_page to read specific sections ...]"
            
            header = f"Reading PDF: {file_path}\n"
            header += f"Pages: {start} to {end} of {total_pages}\n"
            header += f"Characters extracted: {min(len(full_text), max_chars)}\n"
            header += "-" * 50 + "\n"
            
            return header + full_text
            
        except ImportError:
            return "Error: PyPDF2 library is not installed. Please install it with: pip install PyPDF2"
        except Exception as e:
            return f"Error reading PDF '{file_path}': {str(e)}"