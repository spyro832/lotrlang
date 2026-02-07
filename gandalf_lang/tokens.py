from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Token:
    type: str
    value: Any
    line: int
    col: int

class GandalfError(Exception):
    """Base error for the language."""

class LexError(GandalfError):
    def __init__(self, msg: str):
        super().__init__(f"The spell backfires: {msg}")

class ParseError(GandalfError):
    def __init__(self, msg: str):
        super().__init__(f"The rune is unclear: {msg}")

class RuntimeError(GandalfError):
    def __init__(self, msg: str):
        super().__init__(f"The spell backfires: {msg}")
