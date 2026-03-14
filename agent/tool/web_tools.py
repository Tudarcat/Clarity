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
        return "Search for academic papers using Crossref API. Returns paper titles, authors, years, and DOIs."

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="string",
                description="Search query string (keywords, title, author, etc.)",
                required=True
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
                description="Sort order: 'relevance', 'published', 'published-print', etc. Default is 'relevance'.",
                required=False,
                default="relevance"
            ),
            ToolParameter(
                name="order",
                type="string",
                description="Sort direction: 'asc' or 'desc'. Default is 'desc'.",
                required=False,
                default="desc"
            )
        ]

    def execute(self, **kwargs) -> str:
        self.validate_parameters(**kwargs)
        
        query = kwargs.get("query")
        rows = min(kwargs.get("rows", 10), 100)  # Max 100
        offset = kwargs.get("offset", 0)
        sort = kwargs.get("sort", "relevance")
        order = kwargs.get("order", "desc")
        
        try:
            results = self._search_papers(query, rows, offset, sort, order)
            return self._format_results(results, query, rows, offset)
        except Exception as e:
            return f"Error searching papers: {str(e)}"

    def _search_papers(self, query: str, rows: int, offset: int, sort: str, order: str) -> Dict[str, Any]:
        """
        Search papers using Crossref API.
        
        :param query: Search query string
        :param rows: Number of results to return
        :param offset: Offset for pagination
        :param sort: Sort field
        :param order: Sort order
        :return: API response as dictionary
        """
        base_url = "https://api.crossref.org/works"
        
        params = {
            "query": query,
            "rows": rows,
            "offset": offset,
            "sort": sort,
            "order": order
        }
        
        query_string = parse.urlencode(params)
        url = f"{base_url}?{query_string}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        req = request.Request(url, headers=headers)
        
        with request.urlopen(req, timeout=30) as response:
            charset = response.headers.get_content_charset() or 'utf-8'
            data = response.read().decode(charset, errors='ignore')
            return json.loads(data)

    def _format_results(self, results: Dict[str, Any], query: str, rows: int, offset: int) -> str:
        """
        Format search results into a readable string.
        
        :param results: API response dictionary
        :param query: Original search query
        :param rows: Number of rows requested
        :param offset: Offset used
        :return: Formatted results string
        """
        message = results.get("message", {})
        total_results = message.get("total-results", 0)
        items = message.get("items", [])
        
        output = []
        output.append("=" * 60)
        output.append(f"Paper Search Results")
        output.append("=" * 60)
        output.append(f"Query: {query}")
        output.append(f"Total results: {total_results}")
        output.append(f"Showing: {offset + 1}-{min(offset + rows, total_results)} of {total_results}")
        output.append("=" * 60)
        
        if not items:
            output.append("\nNo papers found for this query.")
            return "\n".join(output)
        
        for i, item in enumerate(items, 1):
            output.append(f"\n[{i}]")
            output.append("-" * 40)
            
            # Title
            title = item.get("title", ["N/A"])[0] if item.get("title") else "N/A"
            output.append(f"Title: {title}")
            
            # Authors
            authors = item.get("author", [])
            if authors:
                author_names = []
                for author in authors[:5]:  # Limit to first 5 authors
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
            
            # Year
            published_date = item.get("published-print", item.get("published-online", {}))
            date_parts = published_date.get("date-parts", [[]])[0] if published_date else []
            year = date_parts[0] if date_parts else None
            
            if not year:
                # Try created date
                created = item.get("created", {})
                date_parts = created.get("date-parts", [[]])[0] if created else []
                year = date_parts[0] if date_parts else "N/A"
            
            output.append(f"Year: {year}")
            
            # DOI
            doi = item.get("DOI", "N/A")
            output.append(f"DOI: {doi}")
            
            # URL
            url = item.get("URL", f"https://doi.org/{doi}" if doi != "N/A" else "N/A")
            output.append(f"URL: {url}")
            
            # Container (Journal/Conference)
            container = item.get("container-title", [""])[0] if item.get("container-title") else ""
            if container:
                output.append(f"Published in: {container}")
            
            # Type
            pub_type = item.get("type", "")
            if pub_type:
                output.append(f"Type: {pub_type}")
        
        return "\n".join(output)
