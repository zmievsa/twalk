# Features
twalk packs an entire directory tree (including files) into a single .txt file, which it then can use to regenerate that directory tree.

# Usage
```
usage: twalk [-h] [-i] [-v] [-V | -s] {pack,unpack} path

Condense a directory tree into a single txt file or extract it from one

positional arguments:
  {pack,unpack}        What to do with the specified path
  path                 path to directory you wish to (un)pack

optional arguments:
  -h, --help           show this help message and exit
  -i, --ignore_binary  Instead of raising an exception when encountering binary files during packing, skip them altogether
  -v, --version
  -V, --verbose
  -s, --silent
```
