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
                message = spark(
                    line[1:].decode("unicode_escape").replace("\n", ""),
                    [Misc.faint],
                )
                print(f"{tag} {message}")
            case b"=":
                tag = spark(" NOTI ", [Background.bright_cyan, Misc.italic])
                message = spark(
                    line[1:].decode("unicode_escape").replace("\n", ""),
                    [Misc.faint],
                )
                print(f"{tag} {message}")
            case b"^":
                tag = spark(" DONE ", [Background.bright_green, Misc.italic])
                message = spark(
                    line[1:].decode("unicode_escape").replace("\n", ""),
                    [Misc.faint],
                )
                print(f"{tag} {message}")
            case _:
                tag = spark(" UNKN ", [Background.bright_red, Misc.bold])
                message = spark(
                    line[1:].decode("unicode_escape").replace("\n", ""),
                    [Misc.faint],
                )
                print(f"{tag} {message}")


async def main() -> None:
    process = await create_subprocess_exec(
        "gdb",
        "--interpreter=mi4",
        "--quiet",
        "target",
        stdin=PIPE,
        stdout=PIPE,
    )
    output = await process.stdout.readuntil(b"(gdb)")
    lex_mi_output(output)

    process.stdin.write(b"-symbol-info-functions\n")
    output = await process.stdout.readuntil(b"(gdb)")
    lex_mi_output(output)


if __name__ == "__main__":
    run(main=main())
