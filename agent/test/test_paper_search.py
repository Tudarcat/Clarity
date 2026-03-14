"""
Test the PaperSearchTool.
"""
from agent.tool.web_tools import PaperSearchTool


def test_paper_search():
    print("=" * 60)
    print("Testing PaperSearchTool")
    print("=" * 60)
    
    search_tool = PaperSearchTool()
    
    # Test basic search
    print("\n1. Testing basic search (machine learning):")
    result = search_tool.execute(
        query="machine learning",
        rows=3
    )
    print(result)
    
    # Test search with pagination
    print("\n" + "=" * 60)
    print("2. Testing search with offset (rows=2, offset=2):")
    result = search_tool.execute(
        query="artificial intelligence",
        rows=2,
        offset=2
    )
    print(result)


def test_search_by_author():
    print("\n" + "=" * 60)
    print("Testing search by author")
    print("=" * 60)
    
    search_tool = PaperSearchTool()
    
    print("\n3. Testing search by author:")
    result = search_tool.execute(
        query="author:Hinton deep learning",
        rows=3
    )
    print(result)


def test_search_sorting():
    print("\n" + "=" * 60)
    print("Testing search with different sorting")
    print("=" * 60)
    
    search_tool = PaperSearchTool()
    
    print("\n4. Testing search sorted by published date (desc):")
    result = search_tool.execute(
        query="neural networks",
        rows=3,
        sort="published",
        order="desc"
    )
    print(result)


def test_tool_schema():
    print("\n" + "=" * 60)
    print("Testing PaperSearchTool Schema")
    print("=" * 60)
    
    search_tool = PaperSearchTool()
    schema = search_tool.to_openai_tool()
    
    print(f"\nTool name: {search_tool.name}")
    print(f"Tool description: {search_tool.description}")
    print(f"Parameters: {[p.name for p in search_tool.parameters]}")
    print("\nOpenAI tool schema:")
    import json
    print(json.dumps(schema, indent=2))


def test_no_results():
    print("\n" + "=" * 60)
    print("Testing search with no results")
    print("=" * 60)
    
    search_tool = PaperSearchTool()
    
    print("\n5. Testing search with unlikely query:")
    result = search_tool.execute(
        query="xyzabc123nonexistentpaper",
        rows=5
    )
    print(result)


def test_specific_doi():
    print("\n" + "=" * 60)
    print("Testing search for specific paper by DOI")
    print("=" * 60)
    
    search_tool = PaperSearchTool()
    
    print("\n6. Testing search by DOI:")
    result = search_tool.execute(
        query="10.1038/nature14539",  # AlexNet paper
        rows=1
    )
    print(result)


if __name__ == "__main__":
    test_paper_search()
    test_search_by_author()
    test_search_sorting()
    test_tool_schema()
    test_no_results()
    test_specific_doi()
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
