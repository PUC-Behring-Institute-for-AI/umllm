# Evaluations

## Generate random machines

The command below generates 2 machines with 2 states, 2 symbols, initial work tape with 16 symbols, and that halt after 16 cycles.  The machines are written to directory `out`.

```sh
$ ./generate.py 2 --states=2 --symbols=2 --work=16 --cycles=16 --outdir=out
```

## Run machines using LLMs
