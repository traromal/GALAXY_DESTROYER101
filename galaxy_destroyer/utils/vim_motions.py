"""Vim motions - pure functions for cursor movement"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Cursor:
    line: int
    col: int

    def left(self) -> "Cursor":
        if self.col > 0:
            return Cursor(self.line, self.col - 1)
        return self

    def right(self) -> "Cursor":
        return Cursor(self.line, self.col + 1)

    def up(self) -> "Cursor":
        if self.line > 0:
            return Cursor(self.line - 1, self.col)
        return self

    def down(self) -> "Cursor":
        return Cursor(self.line + 1, self.col)

    def equals(self, other: "Cursor") -> bool:
        return self.line == other.line and self.col == other.col


def resolve_motion(
    key: str,
    cursor: Cursor,
    count: int,
    text_lines: list[str],
) -> Cursor:
    result = cursor
    for _ in range(count):
        next_pos = apply_single_motion(key, result, text_lines)
        if next_pos.equals(result):
            break
        result = next_pos
    return result


def apply_single_motion(
    key: str,
    cursor: Cursor,
    text_lines: list[str],
) -> Cursor:
    current_line = text_lines[cursor.line] if cursor.line < len(text_lines) else ""
    line_len = len(current_line)

    switch = {
        "h": lambda: Cursor(cursor.line, max(0, cursor.col - 1)),
        "l": lambda: Cursor(cursor.line, min(line_len, cursor.col + 1)),
        "j": lambda: Cursor(cursor.line + 1, cursor.col),
        "k": lambda: Cursor(max(0, cursor.line - 1), cursor.col),
        "w": lambda: _next_word_start(cursor, text_lines),
        "b": lambda: _prev_word_start(cursor, text_lines),
        "e": lambda: _end_of_word(cursor, text_lines),
        "0": lambda: Cursor(cursor.line, 0),
        "^": lambda: Cursor(cursor.line, _first_non_blank(current_line)),
        "$": lambda: Cursor(cursor.line, line_len),
        "G": lambda: Cursor(len(text_lines) - 1, 0),
    }

    func = switch.get(key)
    if func:
        return func()
    return cursor


def _next_word_start(cursor: Cursor, text_lines: list[str]) -> Cursor:
    if cursor.line >= len(text_lines):
        return cursor

    line = text_lines[cursor.line]

    if cursor.col < len(line) and _is_word_char(line[cursor.col]):
        while cursor.col < len(line) and _is_word_char(line[cursor.col]):
            cursor = Cursor(cursor.line, cursor.col + 1)
    else:
        while cursor.col < len(line) and not _is_word_char(line[cursor.col]):
            cursor = Cursor(cursor.line, cursor.col + 1)

    while cursor.col < len(line) and not _is_word_char(line[cursor.col]):
        cursor = Cursor(cursor.line, cursor.col + 1)

    if cursor.col >= len(line) and cursor.line < len(text_lines) - 1:
        cursor = Cursor(cursor.line + 1, 0)

    return cursor


def _prev_word_start(cursor: Cursor, text_lines: list[str]) -> Cursor:
    if cursor.line >= len(text_lines):
        return cursor

    line = text_lines[cursor.line]

    if cursor.col > 0 and _is_word_char(line[cursor.col - 1]):
        while cursor.col > 0 and _is_word_char(line[cursor.col - 1]):
            cursor = Cursor(cursor.line, cursor.col - 1)
    else:
        while cursor.col > 0 and not _is_word_char(line[cursor.col - 1]):
            cursor = Cursor(cursor.line, cursor.col - 1)

    while cursor.col > 0 and _is_word_char(line[cursor.col - 1]):
        cursor = Cursor(cursor.line, cursor.col - 1)

    return cursor


def _end_of_word(cursor: Cursor, text_lines: list[str]) -> Cursor:
    if cursor.line >= len(text_lines):
        return cursor

    line = text_lines[cursor.line]

    if cursor.col < len(line) and _is_word_char(line[cursor.col]):
        while cursor.col < len(line) and _is_word_char(line[cursor.col]):
            cursor = Cursor(cursor.line, cursor.col + 1)
    else:
        while cursor.col < len(line) and not _is_word_char(line[cursor.col]):
            cursor = Cursor(cursor.line, cursor.col + 1)

    while cursor.col > 0 and _is_word_char(line[cursor.col - 1]):
        cursor = Cursor(cursor.line, cursor.col - 1)

    return Cursor(cursor.line, max(0, cursor.col - 1))


def _first_non_blank(line: str) -> int:
    for i, char in enumerate(line):
        if not char.isspace():
            return i
    return 0


def _is_word_char(char: str) -> bool:
    return char.isalnum() or char == "_"


def is_inclusive_motion(key: str) -> bool:
    return key in "eE$"


def is_linewise_motion(key: str) -> bool:
    return key in "jkG"
