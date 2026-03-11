"""
Test the ToolBase class and related classes.
"""
from agent.tool import ToolBase, ToolParameter, ToolSchema


class MockTool(ToolBase):
    """
    A mock tool for testing purposes.
    """

    @property
    def name(self) -> str:
        return "mock_tool"

    @property
    def description(self) -> str:
        return "A mock tool for testing"

    @property
    def parameters(self) -> list:
        return [
            ToolParameter(
                name="query",
                type="string",
                description="The query to process",
                required=True
            ),
            ToolParameter(
                name="count",
                type="integer",
                description="The number of results to return",
                required=False,
                default=5
            )
        ]

    def execute(self, **kwargs) -> str:
        self.validate_parameters(**kwargs)
        query = kwargs.get("query")
        count = kwargs.get("count", 5)
        return f"Processed '{query}' with count={count}"


def test_tool_schema():
    tool = MockTool()
    schema = tool.get_schema()
    
    print("Tool name:", schema.name)
    print("Tool description:", schema.description)
    print("Parameters:", [p.name for p in schema.parameters])
    
    openai_tool = tool.to_openai_tool()
    print("\nOpenAI tool format:")
    import json
    print(json.dumps(openai_tool, indent=2))


def test_tool_execution():
    tool = MockTool()
    
    result = tool.execute(query="test query")
    print("\nExecution result:", result)
    
    result = tool.execute(query="another query", count=10)
    print("Execution result with count:", result)


def test_parameter_validation():
    tool = MockTool()
    
    try:
        tool.execute()
    except ValueError as e:
        print("\nValidation error (expected):", e)


if __name__ == "__main__":
    test_tool_schema()
    test_tool_execution()
    test_parameter_validation()
    print("\nAll tests passed!")
