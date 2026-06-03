set -x
./generate.py 1 --outdir=./machines.sample2 --states=2 --symbols=2 --work=8 --cycles=60&
./generate.py 1 --outdir=./machines.sample2 --states=2 --symbols=2 --work=16 --cycles=30&
./generate.py 1 --outdir=./machines.sample2 --states=2 --symbols=2 --work=16 --cycles=60&
./generate.py 1 --outdir=./machines.sample2 --states=2 --symbols=2 --work=32 --cycles=60&
./generate.py 1 --outdir=./machines.sample2 --states=2 --symbols=2 --work=64 --cycles=30&
./generate.py 1 --outdir=./machines.sample2 --states=2 --symbols=2 --work=64 --cycles=60&
