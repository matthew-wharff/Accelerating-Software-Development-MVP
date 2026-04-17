from pathlib import Path

import anthropic

from config import ANTHROPIC_API_KEY
from scripts.logger import get_logger

logger = get_logger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "output"
MODEL = "claude-haiku-4-5-20251001"
SYSTEM_PROMPT = (
    "You are a senior Python engineer doing a code review. "
    "Identify specific bugs, style issues, and missing edge cases. "
    "Be concrete — reference line numbers or variable names where possible."
)


def run_critic(file_path: str, conventions: str) -> str:
    """Review a generated Python file and write a markdown feedback report.

    Reads the file at file_path from disk, calls claude-haiku-4-5-20251001 for
    a code review, writes the feedback to /output/feedback_{filename}.md, and
    returns that path. The file content is never stored in LangGraph state.

    Args:
        file_path: Absolute path to the Python file to review.
        conventions: Content of CONVENTIONS.md, injected on every call.

    Returns:
        Absolute path to the written feedback file as a string.

    Raises:
        FileNotFoundError: If file_path does not exist on disk.
        anthropic.APIError: If the Claude API call fails.
    """
    source_path = Path(file_path)

    logger.info("Critic starting review: %s", file_path)

    try:
        source_code = source_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("Critic could not find file: %s", file_path)
        raise

    user_prompt = (
        f"Review the following Python file: `{source_path.name}`\n\n"
        f"## Project Conventions\n\n{conventions}\n\n"
        f"## File Contents\n\n```python\n{source_code}\n```\n\n"
        "Provide a concrete code review. Reference specific line numbers or "
        "variable names. Flag bugs, style violations against the conventions "
        "above, and missing edge cases. Format your response as markdown."
    )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_prompt}],
        )
    except anthropic.APIError as e:
        logger.error("Claude API call failed for %s: %s", file_path, e)
        raise

    first_block = response.content[0]
    if not isinstance(first_block, anthropic.types.TextBlock):
        raise ValueError(f"Unexpected content block type: {type(first_block)}")
    feedback = first_block.text
    logger.debug("Feedback length: %d chars", len(feedback))

    output_path = OUTPUT_DIR / f"feedback_{source_path.stem.removeprefix('generated_')}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(feedback, encoding="utf-8")

    logger.info("Critic wrote feedback: %s", output_path)
    return str(output_path)


if __name__ == "__main__":
    conventions_path = Path(__file__).parent.parent / "context" / "CONVENTIONS.md"
    conventions_content = conventions_path.read_text(encoding="utf-8")

    target = str(Path(__file__).parent.parent / "output" / "main.py")
    feedback_file = run_critic(target, conventions_content)
    print(f"Feedback written to: {feedback_file}")
