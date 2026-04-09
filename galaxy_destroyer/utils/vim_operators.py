"""Vim operators - actions that operate on text"""

from dataclasses import dataclass
from typing import Callable, Optional, Tuple

from .vim_motions import Cursor, resolve_motion, is_inclusive_motion, is_linewise_motion


@dataclass
class Motion:
    name: str
    resolve: Callable


@dataclass
class OperatorResult:
    text: str
    cursor: Cursor
    mode: str


class VimOperator:
    def __init__(self, name: str):
        self.name = name

    def apply(
        self,
        text: str,
        cursor: Cursor,
        motion: Optional[str],
        count: int,
        motion_fn: Optional[Callable] = None,
    ) -> OperatorResult:
        if motion and motion_fn:
            end_cursor = resolve_motion(motion, cursor, count, text.split("\n"))
        else:
            end_cursor = cursor

        return OperatorResult(text=text, cursor=end_cursor, mode="normal")

    def apply_linewise(self, text: str, start: int, end: int) -> OperatorResult:
        return OperatorResult(text=text, cursor=Cursor(start, 0), mode="normal")


class DeleteOperator(VimOperator):
    def apply(
        self,
        text: str,
        cursor: Cursor,
        motion: Optional[str],
        count: int,
        motion_fn: Optional[Callable] = None,
    ) -> OperatorResult:
        lines = text.split("\n")

        if not motion:
            if cursor.col < len(lines[cursor.line]):
                line = lines[cursor.line]
                new_line = line[: cursor.col] + line[cursor.col + 1 :]
                lines[cursor.line] = new_line
            return OperatorResult(text="\n".join(lines), cursor=cursor, mode="normal")

        end = resolve_motion(motion, cursor, count, lines) if motion_fn else cursor

        start_line = min(cursor.line, end.line)
        end_line = max(cursor.line, end.line)

        if is_inclusive_motion(motion or ""):
            end_col = min(end.col + 1, len(lines[end.line]))
        else:
            end_col = end.col

        if start_line == end_line:
            line = lines[start_line]
            lines[start_line] = line[: cursor.col] + line[end_col:]
        else:
            start_content = lines[start_line][: cursor.col]
            end_content = lines[end.line][end_col:]
            lines[start_line] = start_content + end_content
            del lines[start_line + 1 : end_line + 1]

        new_cursor = Cursor(start_line, cursor.col)
        if new_cursor.col > len(lines[new_cursor.line]):
            new_cursor = Cursor(new_cursor.line, len(lines[new_cursor.line]))

        return OperatorResult(text="\n".join(lines), cursor=new_cursor, mode="normal")


class YankOperator(VimOperator):
    def apply(
        self,
        text: str,
        cursor: Cursor,
        motion: Optional[str],
        count: int,
        motion_fn: Optional[Callable] = None,
    ) -> OperatorResult:
        lines = text.split("\n")

        if not motion:
            return OperatorResult(
                text=text, cursor=Cursor(cursor.line, cursor.col + 1), mode="normal"
            )

        end = resolve_motion(motion, cursor, count, lines)

        start_line = min(cursor.line, end.line)
        end_line = max(cursor.line, end.line)
        start_col = min(cursor.col, end.col)
        end_col = max(cursor.col, end.col)

        if is_inclusive_motion(motion or ""):
            end_col = min(end_col + 1, len(lines[end.line]))

        yanked = []
        for i in range(start_line, end_line + 1):
            if i == start_line:
                yanked.append(lines[i][start_col : min(end_col, len(lines[i]))])
            elif i == end_line:
                yanked.append(lines[i][:end_col])
            else:
                yanked.append(lines[i])

        return OperatorResult(text="\n".join(yanked), cursor=cursor, mode="normal")


class PasteOperator(VimOperator):
    def __init__(self):
        super().__init__("paste")
        self._yanked: Optional[str] = None

    def set_yanked(self, text: str):
        self._yanked = text

    def apply(
        self,
        text: str,
        cursor: Cursor,
        motion: Optional[str],
        count: int,
        motion_fn: Optional[Callable] = None,
    ) -> OperatorResult:
        if not self._yanked:
            return OperatorResult(text=text, cursor=cursor, mode="normal")

        lines = text.split("\n")
        yanked_lines = self._yanked.split("\n")

        if len(yanked_lines) == 1:
            line = lines[cursor.line]
            new_line = line[: cursor.col] + yanked_lines[0] + line[cursor.col :]
            lines[cursor.line] = new_line
            new_cursor = Cursor(cursor.line, cursor.col + len(yanked_lines[0]))
        else:
            before = lines[cursor.line][: cursor.col]
            after = lines[cursor.line][cursor.col :]
            new_lines = [before + yanked_lines[0]]
            new_lines.extend(yanked_lines[1:-1])
            new_lines.append(yanked_lines[-1] + after)
            lines = lines[: cursor.line] + new_lines + lines[cursor.line + 1 :]
            new_cursor = Cursor(
                cursor.line + len(yanked_lines) - 1, len(yanked_lines[-1])
            )

        return OperatorResult(text="\n".join(lines), cursor=new_cursor, mode="normal")


class ChangeOperator(VimOperator):
    def apply(
        self,
        text: str,
        cursor: Cursor,
        motion: Optional[str],
        count: int,
        motion_fn: Optional[Callable] = None,
    ) -> OperatorResult:
        del_op = DeleteOperator()
        result = del_op.apply(text, cursor, motion, count, motion_fn)
        return OperatorResult(text=result.text, cursor=result.cursor, mode="insert")


class IndentOperator(VimOperator):
    def apply(
        self,
        text: str,
        cursor: Cursor,
        motion: Optional[str],
        count: int,
        motion_fn: Optional[Callable] = None,
    ) -> OperatorResult:
        lines = text.split("\n")

        if not motion:
            end_line = cursor.line
        else:
            end = resolve_motion(motion, cursor, count, lines)
            end_line = max(cursor.line, end.line)

        for i in range(cursor.line, end_line + 1):
            lines[i] = "    " + lines[i]

        return OperatorResult(text="\n".join(lines), cursor=cursor, mode="normal")


OPERATORS = {
    "d": DeleteOperator(),
    "y": YankOperator(),
    "p": PasteOperator(),
    "c": ChangeOperator(),
    ">": IndentOperator(),
    "x": DeleteOperator(),
}


def get_operator(name: str) -> Optional[VimOperator]:
    return OPERATORS.get(name)
