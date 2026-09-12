"""
Small, dependency-light helper functions shared across modules.

Nothing in here should import from other `src` subpackages, to keep
this module safely importable everywhere without circular imports.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


def ensure_dir(path: str | Path) -> Path:
    """Create a directory (and parents) if it doesn't already exist.

    Args:
        path: Directory path to create.

    Returns:
        The `Path` object for the ensured directory.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def stable_hash(text: str, length: int = 12) -> str:
    """Generate a short, deterministic hash for a string.

    Used to derive stable, reproducible IDs (e.g. chunk_id) from content,
    so re-running the pipeline on unchanged text yields identical IDs.

    Args:
        text: Input string to hash.
        length: Number of hex characters to keep from the digest.

    Returns:
        A short hex digest string.
    """
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return digest[:length]


def slugify(text: str) -> str:
    """Convert arbitrary text into a filesystem/ID-safe slug.

    Args:
        text: Input text, e.g. a contract title or clause name.

    Returns:
        Lowercase slug using underscores, safe for filenames and IDs.
    """
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def load_json(path: str | Path) -> Any:
    """Load and parse a JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        The parsed JSON content (dict/list/etc).
    """
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, path: str | Path, indent: int = 2) -> None:
    """Serialize data to a JSON file, creating parent directories as needed.

    Args:
        data: JSON-serializable object.
        path: Destination file path.
        indent: Indentation level for pretty-printing.
    """
    path = Path(path)
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def extract_json_block(text: str) -> str:
    """Extract the first top-level JSON object/array substring from LLM output.

    LLMs frequently wrap JSON in markdown fences or add commentary. This
    performs a best-effort extraction by locating the first `{`/`[` and
    matching brace/bracket, rather than relying on regex alone.

    Args:
        text: Raw LLM response text.

    Returns:
        The extracted JSON substring. If no JSON-like structure is found,
        returns the original text unchanged (caller should handle parse errors).
    """
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text.strip(), flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text.strip()).strip()

    start_idx = None
    open_char, close_char = None, None
    for i, ch in enumerate(text):
        if ch in "{[":
            start_idx = i
            open_char = ch
            close_char = "}" if ch == "{" else "]"
            break

    if start_idx is None:
        return text

    depth = 0
    for i in range(start_idx, len(text)):
        if text[i] == open_char:
            depth += 1
        elif text[i] == close_char:
            depth -= 1
            if depth == 0:
                return text[start_idx : i + 1]

    return text[start_idx:]


@contextmanager
def timer() -> Iterator[dict]:
    """Context manager that measures elapsed wall-clock time in seconds.

    Usage:
        with timer() as t:
            do_work()
        print(t["elapsed_seconds"])

    Yields:
        A dict that gets populated with `elapsed_seconds` on exit.
    """
    result: dict[str, float] = {}
    start = time.perf_counter()
    try:
        yield result
    finally:
        result["elapsed_seconds"] = round(time.perf_counter() - start, 4)


def truncate_text(text: str, max_chars: int = 200) -> str:
    """Truncate text for safe, compact logging.

    Args:
        text: Text to truncate.
        max_chars: Maximum characters to keep.

    Returns:
        Truncated text with an ellipsis suffix if it was cut.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."
