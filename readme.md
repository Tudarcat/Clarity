# Clarity Agent

An intelligent CLI assistant built on the **ReAct pattern** (Reasoning + Acting), powered by LLM with tool-calling capabilities.

## Overview

Clarity is a command-line intelligent agent designed to help users with complex tasks including:
- Academic paper retrieval and search
- File operations (read, write, edit, list directories)
- Web content scraping
- PDF document reading
- Task planning and management
- Dialogue summarization and context compression

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                           │
│                    (cli/main.py)                           │
│               Typer-based command interface                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Agent Core                            │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   ReActLoop │  │ MessageBuilder│  │    Summary       │  │
│  │  (loop.py)  │  │ (message.py)  │  │  (summary.py)    │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Provider Layer                           │
│              (agent/provider/)                             │
│  ┌─────────────────────┐  ┌─────────────────────────────┐  │
│  │   ProviderBase      │  │    CustomProvider           │  │
│  │ (Abstract Base)     │  │  (OpenAI-compatible API)   │  │
│  └─────────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Tool Layer                             │
│                   (agent/tool/)                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │FileTools │ │WebTools  │ │PDFTools  │ │ TaskTools    │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
Clarity/
├── agent/                         # Main agent package
│   ├── __init__.py
│   ├── core/                      # Core agent logic
│   │   ├── loop.py               # ReAct loop implementation
│   │   └── message.py            # System prompt builder
│   ├── provider/                  # LLM provider integration
│   │   ├── provider_base.py      # Abstract provider class
│   │   └── custom_provider.py    # OpenAI-compatible provider
│   ├── tool/                      # Tool system
│   │   ├── tool_base.py         # Base class for all tools
│   │   ├── tool_manager.py      # Tool registration
│   │   ├── file_tools.py       # File operations
│   │   ├── web_tools.py        # Web scraping & paper search
│   │   ├── pdf_tools.py        # PDF reading
│   │   └── task_tools.py       # Task planning
│   ├── test/                      # Unit tests
│   │   ├── test_chat.py
│   │   ├── test_file_tools.py
│   │   ├── test_message.py
│   │   ├── test_paper_search.py
│   │   ├── test_tool.py
│   │   └── test_web_tool.py
│   ├── knowledge/                 # Knowledge base (reserved)
│   │   └── __init__.py
│   └── summary.py                # Dialogue summarization
├── cli/                           # CLI interface
│   ├── __init__.py
│   ├── main.py                   # Main CLI application
│   └── config.py                 # Configuration management
├── main.py                        # Entry point
├── readme.md
└── report_bj.md
```

## Core Components

### 1. ReAct Loop (`agent/core/loop.py`)

The heart of the agent - implements the **ReAct (Reasoning + Acting)** pattern.

**Key Classes:**
- `LoopResult`: Container for loop execution results
- `ReActLoop`: Main loop controller

**How it works:**
```
┌──────────────────────────────────────┐
│         Start Loop (max 20 iter)     │
└──────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│     Call LLM with messages + tools   │
└──────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│   Has tool_calls?                    │
│   ┌────────────┬────────────┐       │
│   │    YES     │     NO     │       │
│   ▼            ▼            │       │
│ Execute      Return         │       │
│ tools,       final_answer    │       │
│ append                       │       │
│ results                      │       │
│   │            │            │       │
│   └────────────┴────────────┘       │
│                │                     │
│                ▼                     │
│         Next iteration               │
└──────────────────────────────────────┘
```

**Key Methods:**
- `run_loop()`: Executes the ReAct loop
- `_handle_tool_calls()`: Parses and executes tool calls from LLM response

### 2. Message Builder (`agent/core/message.py`)

Constructs the system prompt that defines the agent's identity and behavior.

**System Prompt Includes:**
- Agent identity: "You are Clarity, an AI assistant..."
- Policy rules (10 rules for tool usage, behavior guidelines)
- Runtime information (current time, timezone, OS, working directory)

### 3. Provider System (`agent/provider/`)

Abstraction layer for LLM providers.

**ProviderBase (Abstract):**
```python
class ProviderBase(ABC):
    @abstractmethod
    def chat(self, messages, tool_list) -> LLMResponse:
        pass

    @abstractmethod
    def get_max_tokens(self) -> int:
        pass
```

**CustomProvider:**
- Implements OpenAI-compatible API client
- Uses `openai` package
- Supports function calling format
- Returns `LLMResponse` with:
  - `content`: Text response
  - `tool_calls`: List of tool calls (if any)
  - `reasoning_content`: Reasoning trace (if available)
  - `token_usage`: Token consumption stats

### 4. Tool System (`agent/tool/`)

#### Base Class (`tool_base.py`)

All tools inherit from `ToolBase`:

```python
class ToolBase(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    def parameters(self) -> List[ToolParameter]:
        return []

    @abstractmethod
    def execute(self, **kwargs) -> str:
        pass

    def to_openai_tool(self) -> Dict[str, Any]:
        # Converts tool to OpenAI function calling format
        pass
```

#### Available Tools

| Tool | File | Description |
|------|------|-------------|
| `read_file` | file_tools.py | Read file contents with line numbers |
| `write_file` | file_tools.py | Write content to files |
| `edit_file` | file_tools.py | Edit files by replacing content |
| `list_directory` | file_tools.py | List directory contents |
| `scrape_web` | web_tools.py | Scrape and clean web page content |
| `search_papers` | web_tools.py | Search academic papers via Crossref API |
| `read_pdf` | pdf_tools.py | Extract text from PDF documents |
| `update_task` | task_tools.py | Plan and track complex tasks |

#### Tool Manager (`tool_manager.py`)

Registers and manages all available tools:

```python
class ToolManager:
    tools_list = [
        WebScraperTool(),
        EditFileTool(),
        ReadFileTool(),
        WriteFileTool(),
        ListDirectoryTool(),
        PaperSearchTool(),
        UpdateTaskTool(),
        ReadPDFTool()
    ]
```

### 5. Summary System (`agent/summary.py`)

Handles dialogue history compression to manage context length.

**How it works:**
- Triggers when message history exceeds 4 messages
- Extracts key facts, user objectives, completed steps, pending items
- Maintains coherence by summarizing semantic dialogue turns
- Returns compressed context for continued conversation

## CLI Interface (`cli/`)

### Main Application (`main.py`)

Built with **Typer** framework, provides:

**Commands:**
- `/help` - Show help message
- `/clear` - Clear conversation history
- `/config` - Show current configuration
- `/version` - Show version info

**Interactive Features:**
- Rich-formatted output with markdown support
- Command auto-completion
- Real-time streaming of LLM responses
- Thinking indicator during LLM processing

### Configuration (`config.py`)

**Config Structure:**
```python
@dataclass
class Config:
    provider: ProviderConfig
    work_dir: str = "."
    max_iter: int = 20

@dataclass
class ProviderConfig:
    provider_type: str = "doubao"
    model: str = "ep-20260310201337-5k45l"
    api_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    api_key: Optional[str] = None
```

**Config File Location:** `~/.clarity/config.json`

## Usage

### Basic Usage

```bash
# Run the CLI
python main.py

# Or install and run as module
pip install -e .
clarity
```

### Configuration

Create `~/.clarity/config.json`:

```json
{
    "provider": {
        "provider_type": "doubao",
        "model": "your-model-name",
        "api_url": "https://your-api-endpoint.com/api/v3",
        "api_key": "your-api-key"
    },
    "work_dir": ".",
    "max_iter": 20
}
```

### Example Interactions

```
User: Read the contents of test/example.txt
Agent: (calls read_file tool) -> Returns file contents

User: Search for papers about machine learning
Agent: (calls search_papers tool) -> Returns paper list with titles, authors, DOIs

User: Create a task plan for building a web scraper
Agent: (calls update_task tool) -> Returns structured task plan with steps
```

## ReAct Pattern Implementation

The ReAct (Reasoning + Acting) pattern enables the agent to:

1. **Reason**: The LLM thinks about what action to take based on the user's request
2. **Act**: The agent calls external tools to gather information or perform actions
3. **Observe**: Tool results are fed back to the LLM
4. **Reason**: The LLM analyzes the results and decides next steps
5. **Repeat** until task is complete

**Key Advantage**: Unlike simple LLM responses, the agent can:
- Access real-time information (web, files, APIs)
- Perform actual actions (edit files, search papers)
- Handle complex multi-step tasks
- Maintain state across tool calls

## Testing

Unit tests are located in `agent/test/`:

```bash
# Run all tests
python -m pytest agent/test/

# Run specific test
python agent/test/test_file_tools.py
```

## License

Apache License 2.0 - See LICENSE file
