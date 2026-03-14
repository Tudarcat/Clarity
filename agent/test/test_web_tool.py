"""
Test the WebScraperTool.
"""
from agent.tool import WebScraperTool


def test_web_scraper():
    print("=" * 50)
    print("Testing WebScraperTool")
    print("=" * 50)
    
    scraper = WebScraperTool()
    
    # Test basic scraping
    print("\n1. Testing basic scraping:")
    result = scraper.execute(
        url="https://example.com",
        max_length=500
    )
    print(result)
    
    # Test scraping with custom max_length
    print("\n" + "=" * 50)
    print("2. Testing scraping with custom max_length (200):")
    result = scraper.execute(
        url="https://example.com",
        max_length=200
    )
    print(result)



def test_clean_html():
    print("\n" + "=" * 50)
    print("Testing HTML cleaning functionality")
    print("=" * 50)
    
    scraper = WebScraperTool()
    
    # Test HTML with various elements to clean
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
        <meta charset="UTF-8">
        <link rel="stylesheet" href="style.css">
        <style>
            body { color: red; }
        </style>
    </head>
    <body>
        <h1>Main Title</h1>
        <p class="content" id="para1" style="color: blue;" onclick="alert('hi')">
            This is a paragraph with <strong>bold</strong> text.
        </p>
        <script>
            console.log('This should be removed');
        </script>
        <noscript>
            <p>JavaScript is disabled</p>
        </noscript>
        <div data-custom="value">Content with data attribute</div>
        <!-- This is a comment -->
        <iframe src="frame.html"></iframe>
        <svg width="100" height="100">
            <circle cx="50" cy="50" r="40"/>
        </svg>
    </body>
    </html>
    """
    
    cleaned = scraper._clean_html(test_html)
    print("\nCleaned content:")
    print(cleaned)
    print("\n" + "-" * 50)
    print("Verification:")
    print(f"- Contains 'script': {'script' in cleaned.lower()}")
    print(f"- Contains 'style': {'style' in cleaned.lower()}")
    print(f"- Contains 'onclick': {'onclick' in cleaned.lower()}")
    print(f"- Contains 'class=': {'class=' in cleaned.lower()}")
    print(f"- Contains 'id=': {'id=' in cleaned.lower()}")
    print(f"- Contains 'data-custom': {'data-custom' in cleaned.lower()}")
    print(f"- Contains '<!--': {'<!--' in cleaned}")
    print(f"- Contains 'Main Title': {'Main Title' in cleaned}")
    print(f"- Contains 'bold': {'bold' in cleaned}")


def test_link_preservation():
    print("\n" + "=" * 50)
    print("Testing link preservation")
    print("=" * 50)
    
    scraper = WebScraperTool()
    
    # Test HTML with links
    test_html = """
    <html>
    <body>
        <h1>Welcome</h1>
        <p>Visit <a href="https://example.com">Example Site</a> for more info.</p>
        <p>Check out <a href="https://python.org" class="link">Python</a> programming.</p>
        <p>Here is a <a href="/local/path">local link</a> and 
           <a href="https://github.com/user/repo">GitHub Repo</a>.</p>
        <p>Invalid links: <a href="javascript:void(0)">JS link</a>, 
           <a href="#section">Anchor</a>,
           <a href="mailto:test@example.com">Email</a></p>
        <p>Link with nested tags: <a href="https://test.com"><strong>Bold Link</strong></a></p>
    </body>
    </html>
    """
    
    cleaned = scraper._clean_html(test_html)
    print("\nCleaned content with links:")
    print(cleaned)
    print("\n" + "-" * 50)
    print("Verification:")
    print(f"- Contains markdown link format: {'[' in cleaned and '](' in cleaned}")
    print(f"- Contains 'example.com': {'example.com' in cleaned}")
    print(f"- Contains 'python.org': {'python.org' in cleaned}")
    print(f"- Contains 'Links found on page': {'Links found on page' in cleaned}")
    print(f"- No 'javascript:' links: {'javascript:' not in cleaned}")
    print(f"- No 'mailto:' links: {'mailto:' not in cleaned}")


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


def test_error_handling():
    print("\n" + "=" * 50)
    print("Testing error handling")
    print("=" * 50)
    
    scraper = WebScraperTool()
    
    # Test with invalid URL
    print("\n1. Testing with invalid URL:")
    result = scraper.execute(url="not_a_valid_url")
    print(result)
    
    # Test with non-existent domain
    print("\n2. Testing with non-existent domain:")
    result = scraper.execute(url="https://this-domain-does-not-exist-12345.com")
    print(result)


if __name__ == "__main__":
    test_web_scraper()
    test_clean_html()
    test_link_preservation()
    test_tool_schema()
    test_error_handling()
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)
