"""
Test the file tools.
"""
import os
import tempfile
from agent.tool import ReadFileTool, WriteFileTool, EditFileTool, ListDirectoryTool, KnowledgeRepo  


def test_write_and_read_file():
    print("=" * 50)
    print("Testing WriteFileTool and ReadFileTool")
    print("=" * 50)
    
    write_tool = WriteFileTool()
    read_tool = ReadFileTool()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        
        result = write_tool.execute(
            file_path=test_file,
            content="Hello, World!\nThis is a test file.\nLine 3 here."
        )
        print(f"\nWrite result: {result}")
        
        result = read_tool.execute(file_path=test_file)
        print(f"\nRead result:\n{result}")
        
        result = read_tool.execute(file_path=test_file, offset=2, limit=1)
        print(f"\nRead with offset and limit:\n{result}")


def test_edit_file():
    print("\n" + "=" * 50)
    print("Testing EditFileTool")
    print("=" * 50)
    
    write_tool = WriteFileTool()
    edit_tool = EditFileTool()
    read_tool = ReadFileTool()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "edit_test.txt")
        
        write_tool.execute(
            file_path=test_file,
            content="Line 1\nLine 2\nLine 3\n"
        )
        
        print("\nOriginal content:")
        print(read_tool.execute(file_path=test_file))
        
        result = edit_tool.execute(
            file_path=test_file,
            old_content="Line 2",
            new_content="Modified Line 2"
        )
        print(f"\nEdit result: {result}")
        
        print("\nAfter edit:")
        print(read_tool.execute(file_path=test_file))


def test_list_directory():
    print("\n" + "=" * 50)
    print("Testing ListDirectoryTool")
    print("=" * 50)
    
    list_tool = ListDirectoryTool()
    
    result = list_tool.execute(directory_path="d:\\Source\\clarity\\agent")
    print(f"\nList directory result:\n{result}")


def test_tool_schema():
    print("\n" + "=" * 50)
    print("Testing Tool Schemas")
    print("=" * 50)
    
    tools = [ReadFileTool(), WriteFileTool(), EditFileTool(), ListDirectoryTool(), KnowledgeRepo()]
    
    for tool in tools:
        schema = tool.to_openai_tool()
        print(f"\n{tool.name}:")
        print(f"  Description: {tool.description}")
        print(f"  Parameters: {[p.name for p in tool.parameters]}")


if __name__ == "__main__":
    test_write_and_read_file()
    test_edit_file()
    test_list_directory()
    test_tool_schema()
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)
