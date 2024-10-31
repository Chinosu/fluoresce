- Setup Google Cloud VM
- Setup Caddy refresh
<!-- - Setup Nix -->
- create `spark`: abstraction over ansi formatting


## Journal for (1 Nov 0110)

This is our first "checkpoint". By which, we have created a main driver file `dev.py` that currently launches a GDB instance in machine interface v4 mode and parses its output. Specifically, we can use the fact that the command outputs are guarded by the sentinel phrase "(gdb)", so we can asynchronously read from the instance until we find that exact phrase. Using machine interface mode we can categorise the output of the instance, between information, notification, and more. We present the output back the user in a more friendly manner with terminal formatting by writing a custom terminal ANSI formatting library `spark.py`. Demo commands are as follows.

- `python dev.py`
- `python lib/spark.py`
