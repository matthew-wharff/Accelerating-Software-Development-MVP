"""File writer utility for the multi-agent pipeline.

Centralises all disk I/O for generated code: sanitises LLM-produced filenames
to prevent path traversal, creates output directories automatically, and writes
every file to /output/{project_name}/{filename}.

Design constraint: this module is the only place that writes generated source
code to disk. Agents return content; the pipeline calls this module; state
stores the resulting paths — never the content itself.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from scripts.logger import get_logger

logger = get_logger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def sanitize_filename(filename: str) -> str:
    """Return a safe relative path, stripping path-traversal characters.

    Removes ``..`` components, leading slashes, and empty parts so that an
    LLM-generated filename like ``../../etc/passwd`` or ``/abs/path.py``
    cannot escape the output directory.

    Args:
        filename: Raw filename string from LLM output, e.g. ``models/user.py``
            or the adversarial ``../../etc/passwd``.

    Returns:
        A clean relative path string, e.g. ``models/user.py``.

    Raises:
        ValueError: If the filename is empty or resolves to nothing after
            stripping unsafe components.
    """
    parts = PurePosixPath(filename).parts
    safe_parts = [p for p in parts if p not in ("", "..", "/", ".")]
    if not safe_parts:
        raise ValueError(f"Filename {filename!r} is empty or unsafe after sanitisation")
    return "/".join(safe_parts)


def write_project_files(
    files: dict[str, str],
    project_name: str,
    base_dir: Path | None = None,
) -> list[str]:
    """Write a dict of generated files to /output/{project_name}/.

    Each key in ``files`` is a target filename (possibly with subdirectory
    components like ``models/user.py``). Each value is the raw source code.
    Filenames are sanitised before use — see :func:`sanitize_filename`.

    Args:
        files: Mapping of ``{filename: source_code}`` produced by the Coder.
        project_name: Subdirectory under ``base_dir`` that groups all files
            for this pipeline run, e.g. ``"todo_app"``.
        base_dir: Root output directory. Defaults to the repo-level
            ``output/`` folder. Override in tests to use a tmp path.

    Returns:
        List of absolute path strings for every file written to disk.

    Raises:
        ValueError: If ``files`` is empty, ``project_name`` is empty, or a
            filename is unsafe.
        OSError: If a file cannot be written to disk.
    """
    if not files:
        raise ValueError("files dict is empty — nothing to write")
    if not project_name or not project_name.strip():
        raise ValueError("project_name must not be empty")

    base = base_dir or OUTPUT_DIR
    root = base if project_name == "." else base / project_name
    written: list[str] = []

    for raw_name, content in files.items():
        safe_name = sanitize_filename(raw_name)
        dest = root / safe_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        logger.info("file_writer: wrote %s", dest)
        written.append(str(dest))

    return written
