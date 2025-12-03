# font2c

![sample](sample.png)

font2c.py is a small Python script that generates C code for TrueType, OpenType and other fonts supported by FreeType. The generated code can be compiled and linked directly into C programs to enable text drawing without any external libraries. Example C code for using the generated code is included. This is mainly intended for use in embedded systems. based on a [another](https://github.com/rogerdahl/font-to-c) library that needed fixing.


### Dependencies

- Any C compiler
- python3
- pip3

### Installation

```bash
./install.sh
```
### Usage


```bash
./font2c.py [-h] -f FILE [-s SIZE]
```

where `FILE` is the font file you wish to convert and `SIZE` its size in pixels.


### NOTE

To see the result just compile `main.c` after running the script.

```bash
gcc -std=c99 src/main.c
```
