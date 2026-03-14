"""
Test the WebScraperTool directly.
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.tool.web_tools import WebScraperTool


def test_web_scraper():
    print("=" * 50)
    print("Testing WebScraperTool")
    print("=" * 50)
    
    scraper = WebScraperTool()
    
    # Test static scraping with cleaning
    print("\n1. Testing static scraping with cleaning:")
    result = scraper.execute(
        url="https://example.com",
        render_dynamic=False,
        clean_html=True,
        max_length=500
    )
    print(result)
    
    # Test static scraping without cleaning
    print("\n" + "=" * 50)
    print("2. Testing static scraping without cleaning:")
    result = scraper.execute(
        url="https://example.com",
        render_dynamic=False,
        clean_html=False,
        max_length=500
    )
    print(result)


def test_tool_schema():
    print("\n" + "=" * 50)
    print("Testing WebScraperTool Schema")
    print("=" * 50)
    
    scraper = WebScraperTool()
    schema = scraper.to_openai_tool()
    
    print(f"Tool name: {scraper.name}")
    print(f"Tool description: {scraper.description}")
    print(f"Parameters: {[p.name for p in scraper.parameters]}")
    print("\nOpenAI tool schema:")
    import json
    print(json.dumps(schema, indent=2))


if __name__ == "__main__":
    test_web_scraper()
    test_tool_schema()
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)
