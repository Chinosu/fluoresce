from pprint import pp
from gdb import GDB
from contextlib import suppress
from asyncio import run
from collections import deque
from dataclasses import dataclass


@dataclass
class Variable:
    name: str
    address: str


@dataclass
class Address:
    type: str
    value: str


async def info(gdb: GDB, variable: str, frame: int | None = None):
    last_frame = len(await gdb.frames())
    if frame is None:
        frame = last_frame
    code, res = await gdb.run_command(f"-stack-select-frame {frame}")
    assert code == "done", res

    code, res = await gdb.run_command(f"-var-create VARI * {variable}")
    assert code == "done", res
    code, res = await gdb.run_command("-var-info-type VARI")
    assert code == "done", res
    type = res["type"]

    code, res = await gdb.run_command(f"-var-list-children VARI")
    if res["numchild"] == "0":
        children = []
    else:
        children = [
            (child["exp"], child["type"], int(child["numchild"]))
            for child in res["children"]
        ]
    code, res = await gdb.run_command("-var-delete VARI")
    assert code == "done", res

    code, res = await gdb.run_command(f"-data-evaluate-expression {variable}")
    assert code == "done", res
    value = res["value"]

    code, res = await gdb.run_command(f"-data-evaluate-expression &{variable}")
    assert code == "done", res
    address = res["value"]

    code, res = await gdb.run_command(f"-stack-select-frame {last_frame}")
    assert code == "done", res
    return (type, value, address, children)


async def silly(gdb: GDB):
    addresses = {}
    frames = {}

    for i, frame in enumerate(await gdb.frames()):
        frame_info = []
        refs = deque()

        for variable in await gdb.variables(i):
            type, value, address, children = await info(gdb, variable, i)
            frame_info.append(Variable(variable, address))
            addresses[address] = Address(type, value)

            if value == "0x0":
                continue
            for subname, subtype, numsubchildren in children:
                if subtype == "char":
                    # Avoid inspecting each char in every string
                    continue
                if subname.startswith("*"):
                    # It's a pointer
                    refs.append(subname)
                elif subname.isdigit():
                    # It's an array index
                    refs.append(f"{variable}[{subname}]")
                else:
                    # It's a struct field
                    refs.append(f"({variable}.{subname})")

        while refs:
            variable = refs.popleft()
            type, value, address, children = await info(gdb, variable, i)
            if address in addresses:
                continue

            addresses[address] = Address(type, value)
            if value == "0x0":
                continue
            for subname, subtype, numsubchildren in children:
                if subtype == "char":
                    # Avoid inspecting each char in every string
                    continue
                if subname.startswith("*"):
                    # It's a pointer
                    refs.append(subname)
                    continue
                elif subname.isdigit():
                    # It's an array index
                    refs.append(f"{variable}[{subname}]")
                else:
                    # It's a struct field
                    refs.append(f"({variable}.{subname})")

        frames[(i, frame)] = frame_info

    print()
    pp(frames)
    print()
    pp(addresses)


async def main():
    """
    gcc target.c -g -O0 -Wall -Wextra -Werror -o target
    """
    async with GDB("target") as gdb:
        functions = await gdb.functions()
        pp(functions)
        for function in functions:
            pp(await gdb.breakpoint(function))
        pp(await gdb.run())
        for _ in range(50):
            pp(await gdb.next())

        pp(await gdb.frames())
        print()
        pp(await silly(gdb))
        pp(await gdb.next())
        pp(await gdb.variables())
        pp(await gdb.frames())

        with suppress(AssertionError):
            while True:
                pp(await gdb.next())


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        run(main=main())
