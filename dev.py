from asyncio import run, create_subprocess_exec
from subprocess import PIPE
from pprint import pprint

from lib.spark import spark, Background, Foreground, Misc


def lex_mi_output(output: bytes):
    lines = output.splitlines()
    lines.pop()  # skip final line `(gdb)`
    for line in lines:
        match line[0:1]:
            case b"~":
                tag = spark(" INFO ", [Background.white, Misc.italic])
                print(f"{tag} {line}")
            case b"=":
                tag = spark(" NOTI ", [Background.bright_cyan, Misc.italic])
                print(f"{tag} {line}")
            case _:
                tag = spark(" UNKN ", [Background.bright_red, Misc.bold])
                print(f"{tag} {line}")


async def main() -> None:
    process = await create_subprocess_exec(
        "gdb",
        "--interpreter=mi4",
        # "--quiet",
        stdin=PIPE,
        stdout=PIPE,
    )
    output = await process.stdout.readuntil(b"(gdb)")
    lex_mi_output(output)


if __name__ == "__main__":
    run(main=main())
