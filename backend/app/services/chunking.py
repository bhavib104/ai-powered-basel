"""Text cleaning and chunking with page/section metadata preserved."""

from __future__ import annotations

import re
from dataclasses import dataclass

_WS = re.compile(r"[ \t]+")
_HEADING = re.compile(r"^(?:\d+(?:\.\d+)*)[.)]?\s+\S")


@dataclass
class ChunkDraft:
    index: int
    text: str
    page_number: int | None
    section: str | None


def _normalise(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [_WS.sub(" ", line).strip() for line in text.split("\n")]
    return "\n".join(lines)


def _looks_like_heading(paragraph: str) -> bool:
    if len(paragraph) > 90 or paragraph.endswith((".", ":", ";")):
        return False
    return bool(_HEADING.match(paragraph)) or paragraph.isupper()


def chunk_pages(
    pages: list[tuple[int, str]],
    *,
    max_chars: int = 900,
    overlap_chars: int = 150,
) -> list[ChunkDraft]:
    """Chunk page texts, carrying forward the most recent heading as a section."""
    drafts: list[ChunkDraft] = []
    index = 0
    for page_number, raw in pages:
        text = _normalise(raw)
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        section: str | None = None
        buffer = ""

        def flush(buf: str, sec: str | None, page: int) -> None:
            nonlocal index
            if buf.strip():
                drafts.append(ChunkDraft(index=index, text=buf.strip(), page_number=page, section=sec))
                index += 1

        def emit_oversized(paragraph: str, sec: str | None, page: int) -> None:
            """Split a paragraph longer than ``max_chars`` into word-bounded pieces."""
            words = paragraph.split()
            piece = ""
            for word in words:
                candidate = f"{piece} {word}" if piece else word
                if len(candidate) <= max_chars:
                    piece = candidate
                else:
                    flush(piece, sec, page)
                    piece = word
            flush(piece, sec, page)

        for para in paragraphs:
            if _looks_like_heading(para):
                section = para[:200]
                continue
            if len(para) > max_chars:
                flush(buffer, section, page_number)
                buffer = ""
                emit_oversized(para, section, page_number)
                continue
            if len(buffer) + len(para) + 1 <= max_chars:
                buffer = f"{buffer}\n{para}".strip()
            else:
                flush(buffer, section, page_number)
                tail = buffer[-overlap_chars:] if overlap_chars and buffer else ""
                buffer = f"{tail}\n{para}".strip()
        flush(buffer, section, page_number)
    return drafts
