from asyncio import create_task, run, sleep
from collections import deque
from dataclasses import dataclass
import json
from pprint import pp
from contextlib import suppress
from re import sub

from base_gdb import BaseGDB
from spark import Misc, spark, Foreground


@dataclass
class Variable:
    name: str
    address: str
    type: str


@dataclass
class Chunk:
    type: str
    value: str


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
        return [frame["func"] for frame in res["stack"]]

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

    async def variable_info(self, variable: str, frame: int | None = None):
        # The newest/topmost frame is number 0
        code, res = await self.run_command(f"-stack-select-frame {frame or 0}")
        assert code == "done", res

        code, res = await self.run_command(f"-var-create VARI * {variable}")
        assert code == "done", res
        code, res = await self.run_command("-var-info-type VARI")
        assert code == "done", res
        type = res["type"]

        code, res = await self.run_command("-var-list-children VARI")
        if res["numchild"] == "0":
            children = []
        else:
            children = [
                (child["exp"], child["type"], int(child["numchild"]))
                for child in res["children"]
            ]
        code, res = await self.run_command("-var-delete VARI")
        assert code == "done", res

        code, res = await self.run_command(
            f"-data-evaluate-expression {variable}"
        )
        value = res["value"] if code == "done" else ""
        if value.startswith("0x"):
            value = value.split(" ", 1)[0]

        code, res = await self.run_command(
            f"-data-evaluate-expression &{variable}"
        )
        address = res["value"].split(" ", 1)[0] if code == "done" else None

        code, res = await self.run_command(f"-stack-select-frame 0")
        assert code == "done", res
        return (type, value, address, children)

    async def traverse(self):
        addresses = {}
        frames = {}

        for i, frame in enumerate(await self.frames()):
            frame_info = []
            frame_addresses = deque()

            for variable in await self.variables(i):
                type, value, address, children = await self.variable_info(
                    variable, i
                )
                frame_info.append(Variable(variable, address, type))
                addresses[(address, type)] = Chunk(type, _san_value(value))
                _add_children(
                    frame_addresses, variable, (type, value, address, children)
                )

            while frame_addresses:
                variable = frame_addresses.popleft()
                type, value, address, children = await self.variable_info(
                    variable, i
                )
                if (address, type) in addresses:
                    continue
                addresses[(address, type)] = Chunk(type, _san_value(value))
                _add_children(
                    frame_addresses, variable, (type, value, address, children)
                )

            frames[(i, frame)] = frame_info
        return frames, addresses


def _san_value(value: str):
    value = sub(r", '\\000' <repeats \d+ times>", r"", value)
    value = sub(r"'\\000' <repeats \d+ times>", r'"\\\\x00"', value)
    if value.startswith("{"):
        # It's a struct, clean it up
        value = sub(r"([{ ])([^ ]+)  ", r'\1"\2":', value)
    value = sub(r"(0x[a-z0-9]+)", r'"\1"', value)
    value = sub(r"(\d+ '.')", r'"\1"', value)
    with suppress(json.decoder.JSONDecodeError):
        return json.loads(value)
    # If json loads failed, assume values are garbage
    return None


def _add_children(frame_addresses, variable, variable_info):
    type, value, address, children = variable_info
    if value == "0x0":
        return

    for subname, subtype, numsubchildren in children:
        if subtype == "char":
            # Avoid inspecting each char in every string
            continue
        if subname.startswith("*"):
            # It's a pointer
            frame_addresses.append(subname)
        elif subname.isdigit():
            # It's an array index
            frame_addresses.append(f"{variable}[{subname}]")
        elif type.endswith("*"):
            # It's a struct pointer
            frame_addresses.append(f"(*{variable})")
        else:
            # It's a struct field
            frame_addresses.append(f"({variable}.{subname})")


async def main():
    async def log_reader(gdb: GDB):
        async for message in gdb.out_of_band_messages():
            print(spark(message, [Misc.faint, Foreground.blue]))

    async def output_reader(gdb: GDB):
        async for output in gdb.target_output():
            print(spark(f">>> {output}", [Misc.bold, Foreground.green]))

    async with GDB("target.c") as gdb:
        create_task(log_reader(gdb))
        create_task(output_reader(gdb))

        functions = await gdb.functions()
        print(f"found functions: {functions}")
        for function in functions:
            print(f"breakpoint no. {await gdb.breakpoint(function)} added")
        pp(await gdb.run())

        try:
            while True:
                await gdb.next()
                # pp(await gdb.frames())
                # pp(await gdb.variables())
                res = await gdb.traverse()
                print(spark(f"Info at report!", [Foreground.bright_yellow]))
                pp(res)
        except AssertionError as e:
            if "No registers." not in str(e):
                raise e


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        run(main=main())
