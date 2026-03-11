"""
Test the MessageBuilder class.
"""
from agent.core.message import MessageBuilder


def test_runtime_prompt():
    print("=" * 50)
    print("Testing _get_runtime_prompt")
    print("=" * 50)
    
    builder = MessageBuilder(work_dir="d:\\Source\\clarity")
    prompt = builder._get_runtime_prompt("d:\\Source\\clarity")
    
    print(prompt)


if __name__ == "__main__":
    test_runtime_prompt()
    print("\n" + "=" * 50)
    print("Test completed!")
    print("=" * 50)
