import json
import subprocess
from typing import Callable, Any, List, Dict
from anthropic import Anthropic
from anthropic.types import Message, ToolUseBlock, TextBlock
from dotenv import load_dotenv
load_dotenv(".env")


class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict,
        function: Callable[..., Any]
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.function = function

    def to_anthropic_format(self) -> dict:
        return {"name": self.name,
                "description": self.description,
                "input_schema": self.parameters
                }

    def execute(self, **kwargs) -> str:
        return str(self.function(**kwargs))


class Agent:
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.client: Anthropic = Anthropic()
        self.model: str = model
        self.tools: List[Tool] = []  # list of Tool objects
        # dictionary (tool names string -> Tool) for quick lookup
        self.tool_names: Dict[str] = {}
        self.max_iterations: int = 15

    def add_tool(self, tool: Tool):
        self.tools.append(tool)

    def run(self, user_message: str) -> str:
        messages = [{"role": "user", "content": user_message}]
        tools = [t.to_anthropic_format() for t in self.tools]

        for i in range(self.max_iterations):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                tools=tools,
                messages=messages
            )

            # claude finishes the response naturally
            if response.stop_reason == "end_turn":
                return response.content

            print(f"iteration {i}: {response.content}")

            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # claude wants to use tool
            if response.stop_reason == "tool_use":
                tool_result = []
                for block in response.content:
                    if isinstance(block, ToolUseBlock):
                        target_tool = block.name
                        if target_tool in self.tool_names:
                            try:
                                res = self.tool_names[target_tool].execute(
                                    **block.input)
                            except Exception as e:
                                res = f"Error executing tool: {e}"
                        else:
                            res = f"Error: Tool '{target_tool}' not found"
                        tool_result.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": res
                        })
                # append message to messages and move to next iteration
                messages.append({
                    "role": "user",
                    "content": tool_result
                })

            # claude's response is cut off due to max_tokens
            # ask it to continue from there in the next iteration
            elif response.stop_reason == "max_tokens":
                messages.append({
                    "role": "user",
                    "content": "Your response was cut off. Please continue."
                })
        return "Error: Max iterations reached."


#
# Functions for creating Tool objects
#

def create_git_clone_tool() -> Tool:
    """
    Create a tool that clones a git repository.
    """

    def git_clone(repo_url: str, destination: str = None) -> str:
        """
        params:
        - repo_url: web url of git repository
        - destination: where you want to clone the repo to
        """
        cmd = ["git", "clone", repo_url]
        if destination:
            cmd.append(destination)

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return f"Successfully cloned {repo_url}"
        else:
            return f"Error: {result.stderr}"

    return Tool(
        name="git_clone",
        description="Clones a git repository to the local filesystem",
        parameters={
            "type": "object",
            "properties": {
                "repo_url": {
                    "type": "string",
                    "description": "The URL of the repository to clone"
                },
                "destination": {
                    "type": "string",
                    "description": "Optional: where to clone the repo"
                }
            },
            "required": ["repo_url"]
        },
        function=git_clone
    )


def create_read_file_tool() -> Tool:
    """
    Create a tool that reads a file from the repo.
    """

    def read_file(file_path: str) -> str:
        """
        :param file_path: path of the file you want to read
        """
        try:
            with open(file_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: File not found: {file_path}"
        except Exception as e:
            return f"Error reading file: {e}"

    return Tool(
        name="read_file",
        description="Reads the contents of a file",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the file to read"
                }
            },
            "required": ["file_path"]
        },
        function=read_file
    )


def create_write_file_tool() -> Tool:
    """
    Create a tool that writes/modifies a file.
    """
    def write_to_file(file_path: str, content: str):
        """
        params:
        - file_path: Path to the file
        - content: Content to write
        """
        try:
            with open(file_path, "w") as f:
                bytes = f.write(content)
                if bytes == len(content):
                    return f"Succesfully wrote to {file_path}"
                else:
                    return f"Error writing to file Expected write length: {content}, actual length: {bytes}"
        except FileNotFoundError:
            return f"Error: File not found: {file_path}"
        except Exception as e:
            return f"Error writing to file: {e}"

    return Tool(
        name="write_file",
        description="Writes to file",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the file to write to",
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file",
                }
            },
            "required": ["file_path", "content"]
        },
        function=write_to_file
    )


def create_git_commit_tool() -> Tool:
    """
    Create a tool that stages and commits changes.
    """
    def git_commit(message: str, repo_path: str = ".") -> str:
        # stage all changes
        add_result = subprocess.run(
            ["git", "add", "."], capture_output=True, text=True, cwd=repo_path)
        if add_result.returncode != 0:
            return f"Error staging files: {add_result.stderr}"

        # commit
        commit_result = subprocess.run(
            ["git", "commit", "-m", message], capture_output=True, text=True, cwd=repo_path
        )
        if commit_result.returncode == 0:
            return f"Successfully committed: {message}"
        else:
            return f"Error committing: {commit_result.stderr}"

    return Tool(
        name="git_commit",
        description="Stages all changes and creates a commit in the specified repository",
        parameters={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Commit message"
                },
                "repo_path": {
                    "type": "string",
                    "description": "Path to the git repository (default: current directory)"
                }
            },
            "required": ["message"]
        },
        function=git_commit
    )


def create_git_push_tool() -> Tool:
    """
    Create a tool that pushes to remote.
    """
    def git_push(branch: str = "main", repo_path: str = ".") -> str:
        result = subprocess.run(
            ["git", "push", "-u", "origin", branch], capture_output=True, text=True, cwd=repo_path
        )
        if result.returncode == 0:
            return f"Successfully pushed to {branch}"
        else:
            return f"Error pushing: {result.stderr}"

    return Tool(
        name="git_push",
        description="Pushes commit to remote repository",
        parameters={
            "type": "object",
            "properties": {
                "branch": {
                    "type": "string",
                    "description": "Branch to push (default: main)"
                },
                "repo_path": {
                    "type": "string",
                    "description": "Path to the git repository (default: current directory)"
                }
            },
            "required": []
        },
        function=git_push
    )


def create_git_checkout_tool() -> Tool:
    """
    Create a tool that creates and/or checks out a git branch.
    """
    def git_checkout(branch: str, create: bool = False, repo_path: str = ".") -> str:
        cmd = ["git", "checkout"]
        if create:
            cmd.append("-b")
        cmd.append(branch)

        result = subprocess.run(cmd, capture_output=True,
                                text=True, cwd=repo_path)
        if result.returncode == 0:
            action = "Created and switched to" if create else "Switched to"
            return f"{action} branch: {branch}"
        else:
            return f"Error: {result.stderr}"

    return Tool(
        name="git_checkout",
        description="Creates a new branch or switches to an existing branch",
        parameters={
            "type": "object",
            "properties": {
                "branch": {
                    "type": "string",
                    "description": "Name of the branch to checkout or create"
                },
                "create": {
                    "type": "boolean",
                    "description": "If true, create a new branch (git checkout -b)"
                },
                "repo_path": {
                    "type": "string",
                    "description": "Path to the git repository (default: current directory)"
                }
            },
            "required": ["branch"]
        },
        function=git_checkout
    )


def create_pr_tool() -> Tool:
    def create_pr(title: str, body: str, repo_path: str = ".") -> str:
        result = subprocess.run(
            ["gh", "pr", "create", "--title", title, "--body", body],
            capture_output=True,
            text=True,
            cwd=repo_path
        )
        if result.returncode == 0:
            return f"Successfully created PR: {result.stdout}"
        else:
            return f"Error creating PR: {result.stderr}"

    return Tool(
        name="create_pr",
        description="Creates a pull request in the specified repository",
        parameters={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the pull request"
                },
                "body": {
                    "type": "string",
                    "description": "Body of the pull request"
                },
                "repo_path": {
                    "type": "string",
                    "description": "Path to the git repository (default: current directory)"
                }
            },
            "required": ["title", "body"]
        },
        function=create_pr
    )


valid_tools = {
    "create_git_clone_tool": create_git_clone_tool(),
    "create_read_file_tool": create_read_file_tool(),
    "create_write_file_tool": create_write_file_tool(),
    "create_git_commit_tool": create_git_commit_tool(),
    "create_git_push_tool": create_git_push_tool(),
    "create_git_checkout_tool": create_git_checkout_tool(),
    "create_pr_tool": create_pr_tool()
}

if __name__ == "__main__":
    agent = Agent()
    for name, create_func in valid_tools.items():
        tool = create_func
        agent.add_tool(tool)
        agent.tool_names[tool.name] = tool

    user_input = input("Enter your message: ")
    result = agent.run(user_input)
    print(result)
