"""
Test the KnowledgeRepo tool.
"""
from agent.tool.knowledge_repo import KnowledgeRepo


def test_knowledge_repo():
    """
    Test the KnowledgeRepo tool.
    """
    print("=" * 50)
    print("Test KnowledgeRepo tool")
    print("=" * 50)
    tool = KnowledgeRepo()
    print("name:", tool.name)
    print("description:", tool.description)


    print("\n=== Parameters ===")
    for p in tool.parameters:
        print(f"- {p.name} | type={p.type} | required={p.required} | default={p.default}")

    print("\n=== OpenAI Tool Schema ===")
    print(tool.to_openai_tool())
    print("\n=== Execute Test ===")
    result = tool.execute(
        query="帮我找多模态情感分析综述",
        task_type="paper_search",
        domain_hint="academic",
        top_k=3
    )
    print(result)

    print(tool.execute(
        query="PyTorch cross attention docs",
        task_type="web_search",
        domain_hint="python",
        top_k=3
    ))
    print(tool.execute(
        query="loop.py 是做什么的",
        task_type="project_lookup",
        domain_hint="project_internal",
        top_k=3
    ))
    print("\n=== Execute Test with Missing Query ===")
    try:
        tool.execute(task_type="paper_search")
    except Exception as e:
        print("Missing query:", e)
    print("\n=== Execute Test with Unknown Param ===")
    try:
        tool.execute(query="test", unknown="xxx")
    except Exception as e:
        print("Unknown param:", e)
    print("\n=== Execute Test with Valid Query ===")
    print(tool.execute(query="今天天气怎么样"))
    print("\n=== Execute Test with Travelling Recommendation Query ===")
    print(tool.execute(query="推荐我去北京"))


if __name__ == "__main__":
    test_knowledge_repo()