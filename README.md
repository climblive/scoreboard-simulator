# Scoreboard Simulator

Simple tool for simulating climbing competitions running on the clmb.live platform.

## Usage

Create a file `contenders.txt` with one registration code per line.

```
$ cat contenders.txt
NAGRXMAA
5A6LCF7N
F9QCQ57S
6XSASEJF
H33CNFLK
```

Start the simulator. Hit CTRL+C to stop. The simulator shuts down gracefully so shutdown might take a while depending on the configured delay multiplier.

```
$ ./simulator.py contenders.txt
```

To slow down or speed up the simulation you can change the delay multiplier. Default value is 100.