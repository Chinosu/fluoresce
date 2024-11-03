- Setup Google Cloud VM
- Setup Caddy refresh
<!-- - Setup Nix -->
- create `spark`: abstraction over ansi formatting


## Journal for (1 Nov 0110)

This is our first "checkpoint". By which, we have created a main driver file `dev.py` that currently launches a GDB instance in machine interface v4 mode and parses its output. Specifically, we can use the fact that the command outputs are guarded by the sentinel phrase "(gdb)", so we can asynchronously read from the instance until we find that exact phrase. Using machine interface mode we can categorise the output of the instance, between information, notification, and more. We present the output back the user in a more friendly manner with terminal formatting by writing a custom terminal ANSI formatting library `spark.py`. Demo commands are as follows.

- `python dev.py`
- `python lib/spark.py`

## Journal for (2 Nov, 0100)

Created abstraction over GDB/MI with class `GDB`. Reusing much of `dev.py`, it encapsulates GDB commands likelisting functions, creating breakpoints, running, and stepping. We note the mistake of presuming that GDB/MI is exactly synchronous. It is, in actuality, architectured to have a synchronous stream as well as an asynchronous stream. The next task will be to make `GDB` better support those streams. Demo commands are as follows.

- `python lib/gdb.py`

## Journal for (3 Nov, 0400)

Re-architectured class `GDB` to better utilise the async nature of GDB/MI, especially how it has two output streams. By creating multiple threads/coroutines/tasks and assigning one to reading from GDB/MI, writing to it, and the main thread, we can better handle commands without hard-coding the number of async outputs (which is not ideal as the async outputs can technically arise whenever). Next, setup a pseudo-terminal (PTY) device and ask GDB/MI to connect the target executable's input and output to the PTY. This will be much appreciated in the future when we want to interact with the target terminal, i.e., to read its output or to send it input. Additionally, separate `GDB` into `BaseGDB` and `GDB`, where the base class provides lower-level functions that manage threads, processes, and file descriptors, and the standard subclass provides more useful intermediate-level functions like `breakpoint`, `functions`, `run`, `next`, `frames`, and `variables` that are equivalents of GDB/MI's most commonly used commonds. Finally, add an upper-level function is are composed of multiple GDB/MI commands which traverses the memory space, starting from varaibles in each frame and descending via indirection, array indexing, and field accessing like a garbage collector.

- `python silly.py`

- analysing GDB/MI output syntax - token, prefix, body
- synchronous, asynchronous

## Journal for (4 Nov, 0050)

Merged temporary `silly.py` into `gdb.py`. Fixed major issue with `traverse` (the memory space descender) where struct pointers were being implicitly indirected. That is, if we had a struct pointer, `traverse` would descend directly into its fields (i.e., `stct->fld`) and skip the struct itself. Fixing this issue was non-trivial and required the parsing of struct structure to be added. This delve in particular also revelaed more unfixed issues, including some interesting facts about garbage values. Since GDB shows all variables of function (or "frame") even if they haven't been declared and initialized, we inadvertently attempt to access uninitialized values which yield garbage values and destroy our lexers. We have temporarily dealt with initialized garbage using `-ftrivial-auto-var-init=zero`, but have no way to deal with deallocated garbage, and so anticipate a proper fix using a custom-built parser instead of a monkey-patched json parser. Besides this, we are yet to polish the corners of the backend. Most notably, we need proper handling of expected exceptions like the target program exiting as currently it throws an AssertionError, and proper handling of other errors to shut down gracefull and not result in zombie state where multiple SIGINTs are required to terminate the process. We should also question the value of initialising `GDB` with `async with`, as building the frontend has led to a crossways where it is not possible organically initialise `GDB` with `async with`. Specifically, the `async with` statement has to be run in an asyncio event loop. However, `Textual`, the frontend framework, only works if it creates its own event loops, so `GDB` has to be created with too little scope to be useful. The current temporary solution is to manually call `__aenter__` and `__aexit__`. The method used by `BaseGDB` to handle log messages and target output was also changed. To be more "pythonic", they are accessible through an `async for` loop through, for example, `gdb.target_output()`. This allows the consumer code to create separate threads which asynchonosly wait and iterate through output and log messages. The frontend aims to be as simple as possible with a single button and three panels. The first panel contains a preview of the source code, the second panel contains text representing the memory space, and the third panel contains the program's output. Had we had more time, the second panel would have been a visualisation instead of text. There is only one button, which steps through the program, for the sake of simplicity. Should an individual need more control, they are directed to use the Python API instead.
