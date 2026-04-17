import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from pathlib import Path

from agents.critic import run_critic

MVP02_OUTPUT = str(Path(__file__).parent.parent / "output" / "main.py")
CONVENTIONS_PATH = Path(__file__).parent.parent / "context" / "CONVENTIONS.md"


@pytest.mark.integration
def test_run_critic_returns_existing_feedback_file():
    conventions = CONVENTIONS_PATH.read_text(encoding="utf-8")
    result_path = run_critic(MVP02_OUTPUT, conventions)
    assert Path(result_path).exists(), "Feedback file was not created"
    assert Path(result_path).stat().st_size > 0, "Feedback file is empty"


@pytest.mark.integration
def test_run_critic_feedback_is_substantive():
    conventions = CONVENTIONS_PATH.read_text(encoding="utf-8")
    result_path = run_critic(MVP02_OUTPUT, conventions)
    feedback = Path(result_path).read_text(encoding="utf-8")
    assert len(feedback) > 100, "Feedback is unexpectedly short"


def test_run_critic_raises_on_missing_file():
    with pytest.raises(FileNotFoundError):
        run_critic("/nonexistent/path/missing.py", "")
