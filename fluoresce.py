from sys import argv
from asyncio import all_tasks, sleep, run
from typing import Coroutine
from pprint import pformat
from pathlib import Path

from rich.syntax import Syntax
from textual import work
from textual.app import App
from textual.app import ComposeResult
from textual.widgets import Header
from textual.widgets import Button
from textual.widgets import Log
from textual.widgets import Static
from textual.containers import Container
from textual.containers import Horizontal
from textual.containers import VerticalScroll

from base_gdb import parse_result
from gdb import GDB

TEXT = """
    I must not fear.
    Fear is the mind-killer.
    Fear is the little-death that brings total obliteration.
    I will face my fear.
    I will permit it to pass over me and through me.
    And when it has gone past, I will turn the inner eye to see its path.
    Where the fear has gone there will be nothing. Only I will remain.
"""


class Fluoresce(App):
    CSS = """"""

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            with Horizontal():
                with VerticalScroll(id="code-container"):
                    yield Static(id="code")
                yield Log(id="gdb")
                yield Log(id="output")
        yield Button(label="Next", id="next")

    async def on_mount(self) -> None:
        assert len(argv) == 2
        source_path = argv[1]
        self.source = Path(source_path).read_text()
        self.update_code()

        self.gdb = await GDB(source_path).__aenter__()
        functions = await self.gdb.functions()
        for function in functions:
            await self.gdb.breakpoint(function)

        self.read_gdb_logs()
        self.read_target_output()
        await self.gdb.run()

    async def on_app_close(self) -> None:
        await self.gdb.__aexit__(None, None, None)

    async def on_button_pressed(self, event: Button.Pressed):
        match event.button.id:
            case "next":
                await self.gdb.next()
                ret = await self.gdb.traverse()
                self.query_one("#gdb", Log).clear()
                self.query_one("#gdb", Log).write_line(pformat(ret))

    @work
    async def read_gdb_logs(self):
        async for message in self.gdb.out_of_band_messages():
            # self.query_one("#gdb_log", Log).write_line(message)

            code, message = message.split(" ", 1)
            if code == "(*)":
                status, message = message.split(",", 1)
                if status == "stopped":
                    line = int(parse_result(message)["frame"]["line"])
                    self.update_code(line)

    @work
    async def read_target_output(self):
        async for output in self.gdb.target_output():
            self.query_one("#output", Log).write(output.decode())

    def update_code(self, highlight: int | None = None):
        highlight_lines = {highlight} if highlight is not None else {}
        syntax = Syntax(
            code=self.source,
            lexer="c",
            line_numbers=True,
            word_wrap=False,
            indent_guides=True,
            theme="github-dark",
            highlight_lines=highlight_lines,
        )
        self.query_one("#code", Static).update(syntax)
        container = self.query_one("#code-container", VerticalScroll)

        if highlight is not None and not (
            container.scroll_y
            < highlight
            < container.scroll_y + container.size.height
        ):
            container.scroll_to(y=(highlight - 3), immediate=True)


if __name__ == "__main__":
    Fluoresce().run()
