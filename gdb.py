from asyncio import (
    run,
    create_subprocess_exec,
    Queue,
    QueueShutDown,
    create_task,
    gather,
    get_running_loop,
)
from subprocess import PIPE
from re import sub, fullmatch
from pprint import pp
from contextlib import suppress
from os import openpty, ttyname
from select import select
import os
import json

from spark import spark, Foreground, Misc


def remove_array_keys(text: str):
    """
    Removes key-value pairs from arrays, i.e.,

    `[frame={level="0"},frame={level="1"}]`
    becomes
    `[{level="0"},{level="1"}]`
    """

    chars = list[str]()
    brace_stack = ["{"]
    for char in text:
        match char:
            case '"':
                pass
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


def parse_result(text: str):
    text = remove_array_keys(text)
    text = sub(r"([a-zA-Z\-_]+)=", r'"\1":', text)
    try:
        parsed = json.loads(f"{{{text}}}")
    except json.decoder.JSONDecodeError as e:
        print(e)
        with open("z.txt", "wb") as file:
            file.write(text.encode())
        assert False
    return parsed


class BaseGDB:
    def __init__(self, executable_path: str) -> None:
        self.executable_path = executable_path

    async def __aenter__(self):
        self.fd_master, self.fd_slave = openpty()
        self.process = await create_subprocess_exec(
            "gdb",
            "--interpreter=mi4",
            "--quiet",
            "-nx",  # do not execute commands found in init files
            "-nh",  # do not execute commands found in home directory init files
            "--tty",  # alternatively, use command `-inferior-tty-set`
            ttyname(self.fd_slave),
            self.executable_path,
            stdin=PIPE,
            stdout=PIPE,
        )
        self.command_queue = Queue[str]()
        self.result_queue = Queue[tuple[str, dict]]()

        create_task(self._command_writer())
        create_task(self._output_reader())
        create_task(self._target_output_reader())

        return self

    async def _command_writer(self):
        with suppress(QueueShutDown):
            while True:
                command = await self.command_queue.get()
                self.process.stdin.write(f"{command}\n".encode())
                await self.process.stdin.drain()
                self.command_queue.task_done()

    async def _output_reader(self):
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
                    await self.result_queue.put(
                        (result_class, parse_result(result))
                    )
                case _:
                    print(
                        spark(f"({kind})", [Misc.faint, Foreground.blue]),
                        end="",
                    )
                    print(" ", end="")
                    print(
                        spark(
                            f"{message}",
                            [Misc.faint, Foreground.bright_black],
                        ),
                        end="",
                    )
                    print()

    async def _target_output_reader(self):
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
            print(f"[!] read output {output}")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.process.stdin.write_eof()  # or send "-gdb-exit"
        await self.process.stdin.drain()
        # self.process.terminate()
        self.command_queue.shutdown()
        self.result_queue.shutdown()
        await gather(
            self.process.wait(),
            self.command_queue.join(),
            self.result_queue.join(),
        )
        os.close(self.fd_master)
        os.close(self.fd_slave)

    async def run_command(self, command: str):
        await self.command_queue.put(command)
        result_class, result = await self.result_queue.get()
        self.result_queue.task_done()
        return result_class, result


class GDB(BaseGDB):
    async def functions(self) -> list[str]:
        code, res = await self.run_command("-symbol-info-functions")
        assert code == "done", res
        return [
            symbol["name"] for symbol in res["symbols"]["debug"][0]["symbols"]
        ]

    async def breakpoint(self, function: str) -> int:
        code, res = await self.run_command(f"-break-insert {function}")
        assert code == "done", res
        return int(res["bkpt"]["number"])

    async def run(self):
        code, res = await self.run_command("-exec-run")
        assert code == "running", res

    async def next(self):
        code, res = await self.run_command("-exec-next")
        assert code == "running", res

    async def frames(self):
        code, res = await self.run_command("-stack-list-frames")
        assert code == "done", res
        return [frame["func"] for frame in reversed(res["stack"])]

    async def variables(self, frame_index: int | None = None):
        if frame_index is None:
            code, res = await self.run_command(
                "-stack-list-variables --all-values"
            )
        else:
            code, res = await self.run_command(
                f"-stack-list-variables --thread 1 --frame {frame_index} --all-values"
            )
        assert code == "done", res
        return {local["name"]: local["value"] for local in res["variables"]}


async def main():
    async with GDB("target") as gdb:
        functions = await gdb.functions()
        pp(functions)
        for function in functions:
            pp(await gdb.breakpoint(function))
        pp(await gdb.run())
        pp(await gdb.next())
        pp(await gdb.next())
        pp(await gdb.next())
        pp(await gdb.next())
        # pp(await gdb.locals())
        # pp(await gdb.frame())

        # with suppress(AssertionError):
        #     while True:
        #         pp(await gdb.next())


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        run(main=main())
