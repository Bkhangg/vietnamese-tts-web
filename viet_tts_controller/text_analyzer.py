"""
Text analysis engine for Vietnamese TTS.
Splits text into segments with pause metadata.
"""

import re
from typing import List, Tuple, Generator

_SEGMENT_TYPES = [
    "comma",
    "semicolon",
    "colon",
    "period",
    "question",
    "exclamation",
    "ellipsis",
    "paragraph",
    "quotation_start",
    "quotation_end",
    "parenthesis_start",
    "parenthesis_end",
    "dash",
    "sentence_break",
]

_QUOTE_PAIRS = {
    '"': '"',
    "'": "'",
    "\u201c": "\u201d",
    "\u2018": "\u2019",
    "\u00ab": "\u00bb",
    "\u300c": "\u300d",
}

_MULTI_NEWLINE = re.compile(r"\n{2,}")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_ELLIPSIS = re.compile(r"\.{3,}|…")


def _classify_segment(text: str, prev_type: str) -> str:
    """Determine the segment type based on trailing punctuation."""
    stripped = text.rstrip()

    if _ELLIPSIS.search(stripped):
        return "ellipsis"

    if stripped.endswith("?"):
        return "question"
    if stripped.endswith("!"):
        return "exclamation"
    if stripped.endswith(":"):
        return "colon"
    if stripped.endswith(";"):
        return "semicolon"

    stripped = stripped.rstrip(".,!?;:")
    if stripped.endswith(","):
        return "comma"

    if stripped.endswith("."):
        return "period"

    return "sentence_break"


def split_paragraphs(text: str) -> Generator[str, None, None]:
    """Yield paragraphs separated by blank lines."""
    for para in _MULTI_NEWLINE.split(text.strip()):
        para = para.strip()
        if para:
            yield para


def split_sentences(text: str) -> List[Tuple[str, str]]:
    """
    Split text into (segment_text, segment_type) pairs.
    Each pair represents a minimal unit with a trailing pause type.
    """
    segments = []
    para_iter = split_paragraphs(text)
    prev_type = "paragraph"

    for para in para_iter:
        sentences = _SENTENCE_SPLIT.split(para.strip())
        for i, sent in enumerate(sentences):
            sent = sent.strip()
            if not sent:
                continue

            seg_type = _classify_segment(sent, prev_type)
            segments.append((sent, seg_type))
            prev_type = seg_type

        segments.append(("", "paragraph"))

    if segments and segments[-1][1] == "paragraph":
        segments.pop()

    return segments


def split_into_phrases(text: str) -> List[Tuple[str, str]]:
    """
    Finer-grained splitting: break sentences into comma/phrase units.
    """
    segments = split_sentences(text)
    result = []

    for text_part, seg_type in segments:
        if seg_type in ("paragraph", "sentence_break"):
            result.append((text_part, seg_type))
            continue

        parts = re.split(r"([,;:])", text_part)
        buffer = []
        for part in parts:
            if part in (",", ";", ":"):
                clause = "".join(buffer).strip()
                if clause:
                    map_type = {";": "semicolon", ":": "colon"}.get(part, "comma")
                    result.append((clause, map_type))
                buffer = []
            else:
                buffer.append(part)

        remainder = "".join(buffer).strip()
        if remainder:
            result.append((remainder, seg_type))

    return result
