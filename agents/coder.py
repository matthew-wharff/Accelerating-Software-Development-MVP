from pathlib import Path

import anthropic

from config import ANTHROPIC_API_KEY
from scripts.logger import get_logger

logger = get_logger(__name__)

MODEL = "claude-sonnet-4-20250514"


def run_coder(task: dict, conventions: str) -> dict[str, str]:
    """Generate source code for a single file task using Claude.

    Calls claude-sonnet-4-20250514 with a scoped task dict and returns the
    generated source code as a ``{filename: content}`` dict. The caller is
    responsible for writing the content to disk (via ``scripts.file_writer``).
    The generated code is never held in LangGraph state.

    Args:
        task: Dict with keys:
            target_file (str): Filename to generate (e.g. "main.py").
            task_description (str): Plain-English description of what to build.
            relevant_interfaces (str): Signatures only — no implementations.
            dependencies_context (str): Context about upstream dependencies.
        conventions: Content of CONVENTIONS.md, injected on every call.

    Returns:
        Dict mapping the target filename to the generated source code string,
        e.g. ``{"main.py": "def greet(...): ..."}``.

    Raises:
        KeyError: If required task keys are missing.
        anthropic.APIError: If the Claude API call fails.
    """
    target_file: str = task["target_file"]
    task_description: str = task["task_description"]
    relevant_interfaces: str = task.get("relevant_interfaces", "")
    dependencies_context: str = task.get("dependencies_context", "")

    logger.info("Coder starting task: %s", target_file)

    system_prompt = (
        "You are an expert Python developer. "
        "Follow these coding conventions exactly:\n\n"
        f"{conventions}"
    )

    user_prompt = (
        f"Implement the following task.\n\n"
        f"Target file: {target_file}\n"
        f"Task description: {task_description}\n"
    )
    if relevant_interfaces:
        user_prompt += f"\nRelevant interfaces (signatures only):\n{relevant_interfaces}\n"
    if dependencies_context:
        user_prompt += f"\nDependencies context:\n{dependencies_context}\n"
    user_prompt += (
        f"\nReturn ONLY the complete Python source code for `{target_file}`. "
        "No explanations, no markdown fences — just the raw Python code."
    )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_prompt}],
        )
    except anthropic.APIError as e:
        logger.error("Claude API call failed for %s: %s", target_file, e)
        raise

    first_block = response.content[0]
    if not isinstance(first_block, anthropic.types.TextBlock):
        raise ValueError(f"Unexpected content block type: {type(first_block)}")
    generated_code = first_block.text
    logger.info("Coder received %d chars for %s", len(generated_code), target_file)

    return {target_file: generated_code}


if __name__ == "__main__":
    from scripts.file_writer import write_project_files

    conventions_path = Path(__file__).parent.parent / "context" / "CONVENTIONS.md"
    conventions_content = conventions_path.read_text(encoding="utf-8")

    sample_task = {
        "target_file": "main.py",
        "task_description": (
            "Build a CLI todo app with add, list, and done commands. "
            "Store todos in a local JSON file called todos.json."
        ),
        "relevant_interfaces": "",
        "dependencies_context": "",
    }

    code_dict = run_coder(sample_task, conventions_content)
    written_paths = write_project_files(code_dict, project_name="hello_coder")
    for p in written_paths:
        print(f"Generated: {p}")
