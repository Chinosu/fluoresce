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



- analysing GDB/MI output syntax - token, prefix, body
- synchronous, asynchronous
