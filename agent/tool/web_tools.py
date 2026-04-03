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
Web-related tools for the agent system.
"""

import re
import html
import json
from urllib import request, parse
from urllib.error import HTTPError, URLError
from typing import List, Dict, Any, Optional
from agent.tool.tool_base import ToolBase, ToolParameter
try:
    from _version import __version__
except ImportError:
    __version__ = "1.0.0"



class WebScraperTool(ToolBase):
    """
    Tool for scraping web page content using Python standard library.
    """

    @property
    def name(self) -> str:
        return "scrape_web"

    @property
    def description(self) -> str:
        return "Scrape content from a web page and clean HTML by removing JS, CSS and other unnecessary parts."

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="url",
                type="string",
                description="The URL of the web page to scrape.",
                required=True
            ),
            ToolParameter(
                name="max_length",
                type="integer",
                description="Maximum length of the cleaned content. Default is 10000 characters.",
                required=False,
                default=10000
            )
        ]

    def execute(self, **kwargs) -> str:
        self.validate_parameters(**kwargs)
        
        url = kwargs.get("url")
        max_length = kwargs.get("max_length", 10000)
        
        try:
            html_content = self._fetch_html(url)
            cleaned_content = self._clean_html(html_content)
            
            if len(cleaned_content) > max_length:
                cleaned_content = cleaned_content[:max_length] + "\n... (truncated)"
            
            return f"Successfully scraped {url}\n\n{cleaned_content}"
        except Exception as e:
            return f"Error scraping {url}: {str(e)}"

    def _fetch_html(self, url: str) -> str:
        """
        Fetch HTML content from a URL using urllib.
        
        :param url: The URL to fetch content from.
        :return: The HTML content.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        req = request.Request(url, headers=headers)
        
        with request.urlopen(req, timeout=30) as response:
            charset = response.headers.get_content_charset() or 'utf-8'
            return response.read().decode(charset, errors='ignore')

    def _clean_html(self, html_content: str) -> str:
        """
        Clean HTML by removing CSS, JS, and other unnecessary parts using regex,
        while preserving links.
        
        :param html_content: The HTML to clean.
        :return: The cleaned content.
        """
        # Collect all links before cleaning
        links = []
        link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
        
        def collect_link(match):
            href = match.group(1)
            text = re.sub(r'<[^>]+>', '', match.group(2))  # Remove nested tags from link text
            text = html.unescape(text).strip()
            if href and not href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                links.append((text, href))
            return match.group(0)  # Keep the original for now
        
        html_content = re.sub(link_pattern, collect_link, html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove script tags and their content
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove style tags and their content
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove link tags (CSS)
        html_content = re.sub(r'<link[^>]*rel=["\']stylesheet["\'][^>]*>', '', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'<link[^>]*type=["\']text/css["\'][^>]*>', '', html_content, flags=re.IGNORECASE)
        
        # Remove noscript tags
        html_content = re.sub(r'<noscript[^>]*>.*?</noscript>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove iframe tags
        html_content = re.sub(r'<iframe[^>]*>.*?</iframe>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove canvas tags
        html_content = re.sub(r'<canvas[^>]*>.*?</canvas>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove svg tags
        html_content = re.sub(r'<svg[^>]*>.*?</svg>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML comments
        html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
        
        # Remove meta tags
        html_content = re.sub(r'<meta[^>]*>', '', html_content, flags=re.IGNORECASE)
        
        # Remove link tags (except canonical, alternate, etc.)
        html_content = re.sub(r'<link[^>]*>', '', html_content, flags=re.IGNORECASE)
        
        # Remove head section entirely
        html_content = re.sub(r'<head[^>]*>.*?</head>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove inline event handlers
        html_content = re.sub(r'\son\w+=["\'][^"\']*["\']', '', html_content, flags=re.IGNORECASE)
        
        # Remove inline style attributes
        html_content = re.sub(r'\sstyle=["\'][^"\']*["\']', '', html_content, flags=re.IGNORECASE)
        
        # Remove data-* attributes
        html_content = re.sub(r'\sdata-[\w-]+=["\'][^"\']*["\']', '', html_content, flags=re.IGNORECASE)
        
        # Remove class attributes (optional, can be noisy)
        html_content = re.sub(r'\sclass=["\'][^"\']*["\']', '', html_content, flags=re.IGNORECASE)
        
        # Remove id attributes (optional, can be noisy)
        html_content = re.sub(r'\sid=["\'][^"\']*["\']', '', html_content, flags=re.IGNORECASE)
        
        # Convert links to text format [text](url)
        def convert_link(match):
            href = match.group(1)
            text = re.sub(r'<[^>]+>', '', match.group(2))
            text = html.unescape(text).strip()
            if href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                return text  # Just return text for non-http links
            return f"[{text}]({href})"
        
        html_content = re.sub(link_pattern, convert_link, html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Extract text from remaining tags
        # First, add newlines for block-level elements
        html_content = re.sub(r'</(p|div|h[1-6]|li|tr|td|th|blockquote|pre|br|hr)[^>]*>', '\n', html_content, flags=re.IGNORECASE)
        
        # Remove all remaining HTML tags
        html_content = re.sub(r'<[^>]+>', '', html_content)
        
        # Decode HTML entities
        html_content = html.unescape(html_content)
        
        # Clean up whitespace
        html_content = re.sub(r'[ \t]+', ' ', html_content)
        html_content = re.sub(r'\n\s*\n+', '\n\n', html_content)
        html_content = html_content.strip()
        
        # Append collected links section if there are links
        if links:
            html_content += "\n\n---\n\nLinks found on page:\n"
            seen = set()
            for text, href in links:
                if href not in seen:
                    seen.add(href)
                    display_text = text if text else href
                    html_content += f"- [{display_text}]({href})\n"
        
        return html_content


class PaperSearchTool(ToolBase):
    """
    Tool for searching academic papers using Crossref API.
    """

    @property
    def name(self) -> str:
        return "search_papers"

    @property
    def description(self) -> str:
        return "Search for academic papers using Crossref API. Supports general query, author query, title query, and filters. Returns paper titles, authors, years, DOIs, and more."

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="string",
                description="General search query string (fuzzy search across all fields).",
                required=False
            ),
            ToolParameter(
                name="author",
                type="string",
                description="Author name to search for ( searches in author family/given names).",
                required=False
            ),
            ToolParameter(
                name="title",
                type="string",
                description="Title keywords to search for.",
                required=False
            ),
            ToolParameter(
                name="filter",
                type="string",
                description="Filter string in format 'key:value,key:value'. Supported filters: from-pub-date, until-pub-date, from-issued-date, until-issued-date, type, publisher, journal, issn, isbn, doi, funder, prefix, article-number, volume, issue, page, ORCID, member. Example: 'from-pub-date:2020-01-01,type:journal-article'",
                required=False
            ),
            ToolParameter(
                name="rows",
                type="integer",
                description="Number of results to return (max 100). Default is 10.",
                required=False,
                default=10
            ),
            ToolParameter(
                name="offset",
                type="integer",
                description="Offset for pagination (0-based). Default is 0.",
                required=False,
                default=0
            ),
            ToolParameter(
                name="sort",
                type="string",
                description="Sort order: 'relevance', 'published', 'published-print', 'published-online', 'issued', 'created', 'updated'. Default is 'relevance'.",
                required=False,
                default="relevance"
            ),
            ToolParameter(
                name="order",
                type="string",
                description="Sort direction: 'asc' or 'desc'. Default is 'desc'.",
                required=False,
                default="desc"
            ),
            ToolParameter(
                name="select",
                type="string",
                description="Comma-separated list of fields to return. Example: 'DOI,title,author,published'. Default returns all fields.",
                required=False
            )
        ]

    def execute(self, **kwargs) -> str:
        self.validate_parameters(**kwargs)
        
        query = kwargs.get("query", "")
        author = kwargs.get("author", "")
        title = kwargs.get("title", "")
        filter_str = kwargs.get("filter", "")
        rows = min(kwargs.get("rows", 10), 100)
        offset = kwargs.get("offset", 0)
        sort = kwargs.get("sort", "relevance")
        order = kwargs.get("order", "desc")
        select = kwargs.get("select", "")
        
        if not query and not author and not title:
            return "Error: At least one of 'query', 'author', or 'title' parameter must be provided."
        
        try:
            results = self._search_papers(query, author, title, filter_str, rows, offset, sort, order, select)
            return self._format_results(results, query, author, title, filter_str, rows, offset)
        except Exception as e:
            return f"Error searching papers: {str(e)}"

    def _parse_filter(self, filter_str: str) -> Dict[str, str]:
        """
        Parse filter string into a dictionary.
        
        :param filter_str: Filter string in format 'key:value,key:value'
        :return: Dictionary of filter key-value pairs
        """
        if not filter_str:
            return {}
        
        filters = {}
        pairs = filter_str.split(",")
        for pair in pairs:
            if ":" in pair:
                key, value = pair.split(":", 1)
                filters[key.strip()] = value.strip()
        return filters

    def _search_papers(
        self,
        query: str,
        author: str,
        title: str,
        filter_str: str,
        rows: int,
        offset: int,
        sort: str,
        order: str,
        select: str
    ) -> Dict[str, Any]:
        """
        Search papers using Crossref API.
        
        :param query: General search query string
        :param author: Author search query
        :param title: Title search query
        :param filter_str: Filter string
        :param rows: Number of results to return
        :param offset: Offset for pagination
        :param sort: Sort field
        :param order: Sort order
        :param select: Fields to select
        :return: API response as dictionary
        """
        base_url = "https://api.crossref.org/works"
        
        params = {}
        
        if query:
            params["query"] = query
        if author:
            params["query.author"] = author
        if title:
            params["query.title"] = title
        
        if filter_str:
            parsed_filters = self._parse_filter(filter_str)
            params["filter"] = ",".join([f"{k}:{v}" for k, v in parsed_filters.items()])
        
        params["rows"] = rows
        params["offset"] = offset
        params["sort"] = sort
        params["order"] = order
        
        if select:
            params["select"] = select
        
        query_string = parse.urlencode(params)
        url = f"{base_url}?{query_string}"
        
        headers = {
            "User-Agent": f"ClarityBot/{__version__} (mailto:tudarcat@outlook.com)"
        }
        
        req = request.Request(url, headers=headers)
        
        with request.urlopen(req, timeout=30) as response:
            charset = response.headers.get_content_charset() or 'utf-8'
            data = response.read().decode(charset, errors='ignore')
            return json.loads(data)

    def _format_results(
        self,
        results: Dict[str, Any],
        query: str,
        author: str,
        title: str,
        filter_str: str,
        rows: int,
        offset: int
    ) -> str:
        """
        Format search results into a readable string.
        
        :param results: API response dictionary
        :param query: Original search query
        :param author: Author query
        :param title: Title query
        :param filter_str: Filter string
        :param rows: Number of rows requested
        :param offset: Offset used
        :return: Formatted results string
        """
        message = results.get("message", {})
        total_results = message.get("total-results", 0)
        items = message.get("items", [])
        
        output = []
        output.append("=" * 60)
        output.append("Paper Search Results (Crossref API)")
        output.append("=" * 60)
        
        search_desc = []
        if query:
            search_desc.append(f"Query: {query}")
        if author:
            search_desc.append(f"Author: {author}")
        if title:
            search_desc.append(f"Title: {title}")
        if filter_str:
            search_desc.append(f"Filter: {filter_str}")
        output.append(" | ".join(search_desc))
        
        output.append(f"Total results: {total_results}")
        output.append(f"Showing: {offset + 1}-{min(offset + rows, total_results)} of {total_results}")
        output.append("=" * 60)
        
        if not items:
            output.append("\nNo papers found for this query.")
            return "\n".join(output)
        
        for i, item in enumerate(items, 1):
            output.append(f"\n[{i}]")
            output.append("-" * 40)
            
            title = item.get("title", ["N/A"])[0] if item.get("title") else "N/A"
            output.append(f"Title: {title}")
            
            authors = item.get("author", [])
            if authors:
                author_names = []
                for author in authors[:5]:
                    given = author.get("given", "")
                    family = author.get("family", "")
                    if given and family:
                        author_names.append(f"{given} {family}")
                    elif family:
                        author_names.append(family)
                    elif given:
                        author_names.append(given)
                
                author_str = ", ".join(author_names)
                if len(authors) > 5:
                    author_str += f" et al. ({len(authors)} authors total)"
                output.append(f"Authors: {author_str}")
            else:
                output.append("Authors: N/A")
            
            published_date = item.get("published-print", item.get("published-online", {}))
            date_parts = published_date.get("date-parts", [[]])[0] if published_date else []
            year = date_parts[0] if date_parts else None
            
            if not year:
                created = item.get("created", {})
                date_parts = created.get("date-parts", [[]])[0] if created else []
                year = date_parts[0] if date_parts else "N/A"
            
            output.append(f"Year: {year}")
            
            doi = item.get("DOI", "N/A")
            output.append(f"DOI: {doi}")
            
            url = item.get("URL", f"https://doi.org/{doi}" if doi != "N/A" else "N/A")
            output.append(f"URL: {url}")
            
            container = item.get("container-title", [""])[0] if item.get("container-title") else ""
            if container:
                output.append(f"Published in: {container}")
            
            pub_type = item.get("type", "")
            if pub_type:
                output.append(f"Type: {pub_type}")
            
            publisher = item.get("publisher", "")
            if publisher:
                output.append(f"Publisher: {publisher}")
            
            volume = item.get("volume", "")
            if volume:
                output.append(f"Volume: {volume}")
            
            issue = item.get("issue", "")
            if issue:
                output.append(f"Issue: {issue}")
            
            page = item.get("page", "")
            if page:
                output.append(f"Pages: {page}")
            
            issn = item.get("ISSN", "")
            if issn:
                output.append(f"ISSN: {', '.join(issn) if isinstance(issn, list) else issn}")
            
            abstract = item.get("abstract", "")
            if abstract:
                abstract_clean = re.sub(r'<[^>]+>', '', abstract)
                abstract_clean = html.unescape(abstract_clean)
                if len(abstract_clean) > 300:
                    abstract_clean = abstract_clean[:300] + "..."
                output.append(f"Abstract: {abstract_clean}")
            
            subjects = item.get("subject", [])
            if subjects:
                subject_str = ", ".join(subjects[:5])
                if len(subjects) > 5:
                    subject_str += f" and {len(subjects) - 5} more"
                output.append(f"Subjects: {subject_str}")
            
            references_count = item.get("references-count", None)
            if references_count is not None:
                output.append(f"References: {references_count}")
        
        return "\n".join(output)
