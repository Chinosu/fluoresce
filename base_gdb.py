from asyncio import (
    create_subprocess_exec,
    Queue,
    QueueShutDown,
    create_task,
    gather,
    get_running_loop,
)
from subprocess import PIPE
from itertools import pairwise
from re import sub, fullmatch
from contextlib import suppress
from os import openpty, ttyname
from pathlib import Path
import os
import json

TARGET = "TARGET"


class BaseGDB:
    def __init__(self, source_path: str) -> None:
        self.source_path = source_path

    async def __aenter__(self):
        self.fd_master, self.fd_slave = openpty()
        clang = await create_subprocess_exec(
            "clang",
            self.source_path,
            "-o",
            TARGET,
            "-g",
            "-O0",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-ftrivial-auto-var-init=zero",
            # "-enable-trivial-auto-var-init-zero-knowing-it-will-be-removed-from-clang",
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
        )
        stdout, stderr = await clang.communicate()
        exit_code = await clang.wait()
        assert exit_code == 0, ("Compilation failed", stderr)

        self.process = await create_subprocess_exec(
            "gdb",
            "--interpreter=mi4",
            "--quiet",
            "-nx",  # do not execute commands found in init files
            "-nh",  # do not execute commands found in home directory init files
            "--tty",  # alternatively, use command `-inferior-tty-set`
            ttyname(self.fd_slave),
            "--args",
            TARGET,
            "1",
            "2",
            "3",
            "4",
            stdin=PIPE,
            stdout=PIPE,
        )
        self.command_result_queue = Queue[tuple[str, dict]]()
        self.log_queue = Queue[str]()

        create_task(self._result_reader())
        return self

    async def _result_reader(self):
        while True:
            line = await self.process.stdout.readline()
            if not line:
                break
            line = line.strip().decode()
            if line == "(gdb)":
                continue
            kind, message = line[:1], line[1:]
            match kind:
                case "^":
                    if "," not in message:
                        result_class, result = message, ""
                    else:
                        result_class, result = message.split(",", 1)
                    await self.command_result_queue.put(
                        (result_class, parse_result(result))
                    )
                case _:
                    await self.log_queue.put(f"({kind}) {message}")

    async def target_output(self):
        while True:
            """
            alternative, polling approach:

            ```
            os.set_blocking(fd, False)
            while True:
                with suppress(*SomeSpecificError*):
                    output = os.read(fd, 1024)
                    print(f"[!] read output {output}")
                await sleep(1)
            ```
            """

            output = await get_running_loop().run_in_executor(
                None, os.read, self.fd_master, 1024
            )  # `os.read` releases the GIL BTW
            yield output

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.process.stdin.write_eof()  # or send "-gdb-exit"
        await self.process.stdin.drain()
        # self.process.terminate()
        await self.process.wait(),

        self.command_result_queue.shutdown()
        self.log_queue.shutdown(immediate=True)
        await gather(
            self.command_result_queue.join(),
            self.log_queue.join(),
        )

        os.close(self.fd_master)
        os.close(self.fd_slave)
        Path(TARGET).unlink()

    async def run_command(self, command: str):
        self.process.stdin.write(f"{command}\n".encode())
        await self.process.stdin.drain()

        result_class, result = await self.command_result_queue.get()
        self.command_result_queue.task_done()
        return result_class, result

    async def out_of_band_messages(self):
        with suppress(QueueShutDown):
            while True:
                command = await self.log_queue.get()
                self.log_queue.task_done()
                yield command


def parse_result(text: str):
    """
    Crashes sometimes due to results containing junk strings
    because of reading uninitialised and deallocated values
    """
    orig = text

    text = remove_array_keys(text)
    text = sub(r"([a-zA-Z\-_]+)=", r'"\1":', text)
    try:
        parsed = json.loads(f"{{{text}}}")
    except json.decoder.JSONDecodeError as e:
        print(e)
        with open("dump.txt", "ab") as file:
            file.write(orig.encode() + b"\n")
        assert False
    return parsed


def remove_array_keys(text: str):
    """
    Removes key-value pairs from arrays, i.e.,

    `[frame={level="0"},frame={level="1"}]`
    becomes
    `[{level="0"},{level="1"}]`
    """

    chars = list[str]()
    brace_stack = ["{"]

    if text:
        chars.append(text[0])
    for prev, char in pairwise(text):
        if prev != "\\" and brace_stack[-1] == '"':
            if char == '"':
                brace_stack.pop()
        elif prev != "\\":
            match char:
                case '"':
                    brace_stack.append('"')
                case "{":
                    brace_stack.append("{")
                case "}":
                    assert brace_stack[-1] == "{"
                    brace_stack.pop()
                case "[":
                    brace_stack.append("[")
                case "]":
                    assert brace_stack[-1] == "["
                    brace_stack.pop()

        if char != "=" or brace_stack[-1] == "{":
            chars.append(char)
            continue
        while fullmatch(r"[a-zA-Z\-_]", chars[-1]):
            chars.pop()
    return "".join(chars)
