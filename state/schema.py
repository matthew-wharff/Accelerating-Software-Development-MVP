"""LangGraph pipeline state schema.

Design constraint: state stores file paths, NEVER file contents. Generated
code is written to /output/ immediately and referenced by path. This keeps
the state object small, prevents context accumulation, and treats the
filesystem as shared memory.
"""

from __future__ import annotations

from typing import Optional, TypedDict


class TaskEntry(TypedDict):
    """A single coding task from the Architect's ordered task queue.

    Attributes:
        task_id: Unique identifier, e.g. "task_001".
        target_file: Relative path within output/, e.g. "models/user.py".
        description: Spec excerpt for this file only — NOT the full spec.
        interface_refs: Names of interface definitions this task implements.
        dependency_paths: Absolute paths on disk this task depends on.
            The Coder reads signatures from these files, never full source.
    """

    task_id: str
    target_file: str
    description: str
    interface_refs: list[str]
    dependency_paths: list[str]


class TaskLogEntry(TypedDict):
    """Compact completion record for a single coding task.

    Stores only what downstream agents need: status, location on disk,
    and the extracted public interface. Never stores raw source code or
    conversation history.

    Attributes:
        task_id: Matches the corresponding TaskEntry.task_id.
        task_name: Human-readable name, e.g. "Implement UserModel".
        status: One of "complete", "failed", or "in_progress".
        file_path: Absolute path to the generated file on disk.
        interface_signature: Extracted public interface only (function
            signatures, class definitions) — not the full implementation.
    """

    task_id: str
    task_name: str
    status: str
    file_path: str
    interface_signature: str


class E2bOutput(TypedDict):
    """Runtime output captured from e2b sandbox execution.

    Attributes:
        stdout: Standard output from the sandbox run.
        stderr: Standard error from the sandbox run.
        exit_code: Process exit code; 0 indicates success.
    """

    stdout: str
    stderr: str
    exit_code: int


class PipelineState(TypedDict):
    """Central state object shared across all LangGraph nodes.

    Every agent reads from and writes to this object. Fields are designed
    to stay small: list fields accumulate paths or compact log entries,
    never raw file contents or conversation history.

    Attributes:
        project_brief: The original plain-English project description.
        clarified_brief: The brief after the Spec Clarifier has processed it.

        architect_spec_path: Absolute path to architect_spec.md on disk.
            Set by the Architect node; None until then.
        interface_definitions_path: Absolute path to interface_definitions.md
            on disk. Set by the Architect; None until then.
        task_queue: Topologically ordered list of coding tasks produced by
            the Architect. Files with no dependencies come first.

        current_task_index: Index into task_queue pointing to the task the
            Coder is currently working on or will work on next.
        task_log: Compact completion records appended after each coding task.
            Used by the Architect's feedback loop and by the Synthesis Agent.
        generated_file_paths: Absolute paths to every file written to /output/.
            Accumulated across all Ralph Loop iterations.
        task_failure_count: Number of consecutive validation failures for the
            current task. Escalates to the Architect at 3.

        e2b_output: Runtime output from the e2b sandbox execution step.
            Passed to all three critics. None until the sandbox node runs.

        test_feedback_path: Absolute path to test_feedback.md on disk.
            Set by the Test Writer; None until that node runs.
        security_feedback_path: Absolute path to security_feedback.md on disk.
            Set by the Security Reviewer; None until that node runs.
        quality_feedback_path: Absolute path to quality_feedback.md on disk.
            Set by the Code Quality Agent; None until that node runs.

        devops_config_paths: Absolute paths to DevOps output files
            (Dockerfile, ci.yml, docker-compose.yml, .env.example).

        synthesis_report_path: Absolute path to SYNTHESIS_REPORT.md on disk.
            Set by the Synthesis Agent. The Coder reads this on revision passes.

        revision_count: Number of Synthesis → Coder revision loops completed.
            The conditional edge routes to output when this reaches 2.
        task_failure_count: Consecutive validation failures for the current
            task. Resets when a new task begins; escalates to Architect at 3.
        status: Overall pipeline status. One of "running", "complete", "failed".
    """

    # Input
    project_brief: str
    clarified_brief: str

    # Architect artifacts — paths only, never content
    architect_spec_path: Optional[str]
    interface_definitions_path: Optional[str]
    task_queue: list[TaskEntry]

    # Coder progress
    current_task_index: int
    task_log: list[TaskLogEntry]
    generated_file_paths: list[str]
    task_failure_count: int

    # Sandbox
    e2b_output: Optional[E2bOutput]

    # Critic feedback — paths only
    test_feedback_path: Optional[str]
    security_feedback_path: Optional[str]
    quality_feedback_path: Optional[str]

    # DevOps
    devops_config_paths: list[str]

    # Synthesis
    synthesis_report_path: Optional[str]

    # Pipeline control
    revision_count: int
    status: str


def default_state(project_brief: str = "") -> PipelineState:
    """Return a PipelineState initialised with safe defaults.

    TypedDict does not support field-level defaults, so all initial values
    live here. Pass ``project_brief`` when starting a new pipeline run.

    Args:
        project_brief: The plain-English project description submitted by the
            user. Defaults to an empty string for testing convenience.

    Returns:
        A fully-populated PipelineState dict ready to be passed to
        ``graph.invoke()``.
    """
    return PipelineState(
        project_brief=project_brief,
        clarified_brief="",
        architect_spec_path=None,
        interface_definitions_path=None,
        task_queue=[],
        current_task_index=0,
        task_log=[],
        generated_file_paths=[],
        task_failure_count=0,
        e2b_output=None,
        test_feedback_path=None,
        security_feedback_path=None,
        quality_feedback_path=None,
        devops_config_paths=[],
        synthesis_report_path=None,
        revision_count=0,
        status="running",
    )
