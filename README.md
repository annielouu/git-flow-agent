# Minimal Agentic Framework

A simple, well-documented agentic framework to help you learn how AI agents work.

## What is an Agentic Framework?

An **agent** is an AI system that can:
1. **Think** - Understand what needs to be done
2. **Act** - Use tools to interact with the world
3. **Observe** - Process the results of its actions
4. **Iterate** - Repeat until the task is complete

```
┌─────────────────────────────────────────┐
│  User: "What's 25 * 47?"                │
│              ↓                          │
│  ┌────────────────┐                     │
│  │   🧠 THINK     │ → "I need to        │
│  │                │    use calculator"  │
│  └───────┬────────┘                     │
│          ↓                              │
│  ┌────────────────┐                     │
│  │   🔧 ACT       │ → calculator(25*47) │
│  └───────┬────────┘                     │
│          ↓                              │
│  ┌────────────────┐                     │
│  │   👁️ OBSERVE   │ → Result: 1175     │
│  └───────┬────────┘                     │
│          ↓                              │
│  ┌────────────────┐                     │
│  │   🧠 THINK     │ → "I have the       │
│  │                │    answer now"      │
│  └───────┬────────┘                     │
│          ↓                              │
│  Agent: "25 * 47 = 1175"                │
└─────────────────────────────────────────┘
```

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### 3. Run the demo

```bash
python agent.py
```

## Understanding the Code

### The Tool Class

Tools are functions the agent can call. Each tool has:

```python
Tool(
    name="calculator",           # Unique identifier
    description="Does math...",  # Helps LLM decide when to use it
    parameters={...},            # JSON Schema for inputs
    function=my_function         # The actual Python function
)
```

### The Agent Class

The agent orchestrates the loop:

```python
agent = Agent()
agent.add_tool(create_calculator_tool())
result = agent.run("What is 10 + 5?")
```

### Creating Your Own Tools

```python
def create_my_tool() -> Tool:
    def my_function(param1: str, param2: int) -> str:
        # Your logic here
        return f"Result: {param1} repeated {param2} times"

    return Tool(
        name="my_tool",
        description="Describe what your tool does",
        parameters={
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "What this parameter is for"
                },
                "param2": {
                    "type": "integer",
                    "description": "What this parameter is for"
                }
            },
            "required": ["param1", "param2"]
        },
        function=my_function
    )
```

## Key Concepts to Learn

### 1. The Agent Loop
The core pattern: Think → Act → Observe → Repeat

### 2. Tool Use
How LLMs decide which tools to use and how to call them

### 3. Conversation History
The agent maintains context by tracking the full conversation

### 4. Stop Conditions
How the agent knows when to stop (final answer vs. need more tools)

## Exercises

Try these to deepen your understanding:

1. **Add a new tool**: Create a tool that looks up information (mock or real API)
2. **Add memory**: Store conversation history across multiple `run()` calls
3. **Add error handling**: What happens if a tool fails?
4. **Add streaming**: Show Claude's thinking in real-time
5. **Multi-agent**: Create multiple agents that can talk to each other

## Architecture

```
agentic_framework/
├── agent.py          # Main framework code
├── requirements.txt  # Dependencies
└── README.md         # This file
```

## Next Steps

Once you understand this framework, explore:
- **LangChain** - Popular full-featured framework
- **AutoGPT** - Autonomous agent example
- **Claude's tool use docs** - Deep dive into tool calling
