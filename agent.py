import json
import subprocess
from typing import Callable, Any, List, Dict
from anthropic import Anthropic, beta_tool
from anthropic.types import Message, ToolUseBlock, TextBlock
from dotenv import load_dotenv
load_dotenv(".env")

MAX_TOKENS = 1024
BETA_FLAGS = ["advanced-tool-use-2025-11-20"]


@beta_tool
def git_clone(repo_url: str, destination: str = None) -> str:
    """
    Clones a github repository defined by repo_url to a local directory defined by destination.

    Args:
    - repo_url: web url of git repository
    - destination (optional): where you want to clone the repo to. Defualts to current directory.
    """

    cmd = ["git", "clone", repo_url]
    if destination:
        cmd.append(destination)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        return f"Successfully cloned {repo_url}"

    else:
        return f"Error: {result.stderr}"


@beta_tool
def read_file(file_path: str) -> str:
    """
    Reads a file from file_path

    Args:
    file_path: path of the file you want to read
    """
    try:
        with open(file_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error reading file: {e}"


@beta_tool
def write_to_file(file_path: str, content: str):
    """
    Writes content to the file at file_path.

    Args:
    - file_path: Path to the target file
    - content: Content you want to write
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


@beta_tool
def git_commit(message: str, repo_path: str = ".") -> str:
    """
    Commits changes you made to a local git repository at repo_path, and writes a commit message.

    Args:
    - repo_path: path to the git repo
    - message: commit message
    """
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


@beta_tool
def git_push(branch: str = "main", repo_path: str = ".") -> str:
    """
    Pushes changes you made locally to remote git repo
    Args:
    - branch: the remote branch you want to push to
    - repo_path: path to the local git repo
    """
    result = subprocess.run(
        ["git", "push", "-u", "origin", branch], capture_output=True, text=True, cwd=repo_path
    )
    if result.returncode == 0:
        return f"Successfully pushed to {branch}"
    else:
        return f"Error pushing: {result.stderr}"


@beta_tool
def git_checkout(branch: str, create: bool = False, repo_path: str = ".") -> str:
    """
    Checks out a branch at repo_path

    Args:
    - branch: branch you want to push to
    - create: Set to True if you allow the creation of the new branch if it doesn't exist. False otherwise.
    - repo_path: path to the git repo
    """
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


@beta_tool
def create_pr(title: str, body: str, repo_path: str = ".") -> str:
    """
    Creates a pull request.

    Args:
    title: title of the pull request
    body: body content of the pull request
    repo_path: path to the git repo
    """
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


TOOLS = [git_clone, git_push, git_commit, git_checkout, create_pr]


class Agent:
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.client: Anthropic = Anthropic()
        self.model: str = model
        self.tools: List[Callable] = TOOLS
        self.max_iterations: int = 15

    def run(self, user_message: str) -> str:
        messages = [{"role": "user", "content": user_message}]

        runner = self.client.beta.messages.tool_runner(
            model=self.model,
            max_tokens=MAX_TOKENS,
            tools=self.tools,
            messages=messages,
            max_iterations=self.max_iterations,
            betas=BETA_FLAGS
        )
        final_message = runner.until_done()
        return final_message.content


if __name__ == "__main__":
    agent = Agent()

    user_input = input("Enter your message: ")
    result = agent.run(user_input)
    print(result)
