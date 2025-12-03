#!./bin/python

# TODO: Make it compile the --test, there are issues with env and #include when compiling from python.

import argparse
import math
import re
import os
import freetype
from distutils.ccompiler import new_compiler

FIRST_CHAR = " "
LAST_CHAR = "~"
TAB_STR = " " * 4
DEBUG: bool = False

parser = argparse.ArgumentParser(
    prog="font2c.py", description="Convert TTF fonts to C array for embedded devices"
)
parser.add_argument("-f", "--file", required=True, help="The intended file to parse")
parser.add_argument("-s", "--size", default=16, help="Font bit size. Defaults to 16")
parser.add_argument(
    "-t",
    "--test",
    action=argparse.BooleanOptionalAction,
    default=False,
    help="Output an image to see the results. Defaults to false.",
)


def main():
    args = parser.parse_args()
    if args.file is None:
        print(parser.format_help())
        exit(1)
    if int(args.size) % 8 != 0:
        parser.print_usage()
        print("Font sizes must be multiples of 8")
        exit(1)

    generator = Font2ArrayGenerator(args.file, int(args.size), args.test)

    if False:
        if args.test:
            try:
                compiler = new_compiler()
                compiler.compile(["src/main.c", generator.c_file.name])
            except:
                exit(1)


class Font2ArrayGenerator(object):
    def __init__(self, ttf_file: str, pixel_size: int, should_compile: bool):
        self.font_h_filename = "src/font_out.h"
        self.ttf_input_file = ttf_file
        self.pixel_size: int = pixel_size
        self.face = freetype.Face(ttf_file)
        self.face.set_pixel_sizes(0, pixel_size)
        self.h_file = open(self._get_header_name(), "w")
        self.c_file = open(self._get_source_name(), "w")
        self.generate_c_header()
        self.generate_c_source()
        if should_compile and os.path.exists(self.font_h_filename):
            os.remove(self.font_h_filename)
        if should_compile:
            self.font_h_file = open(self.font_h_filename, "w")
            self.generate_font_header()

    def generate_font_header(self):
        self.font_h_file.write(f"#ifndef FONT_OUT_{self._get_safe_name().upper()}_H\n")
        self.font_h_file.write(
            f"#define FONT_OUT_{self._get_safe_name().upper()}_H\n\n"
        )
        self.font_h_file.write('#include "../{}"\n\n'.format(self.h_file.name))
        self.font_h_file.write('#include "../{}"\n\n'.format(self.c_file.name))
        self.font_h_file.write(f"#define font_lookup {self._get_safe_name()}_lookup\n")
        self.font_h_file.write(f"#define font_pixels {self._get_safe_name()}_pixels\n")
        self.font_h_file.write(f"\n#endif // !FONT_{self._get_safe_name().upper()}_H\n")

    def generate_c_header(self):
        self.h_file.write(f"#ifndef {self.c_file.name.upper().split('.')[0]}_H\n")
        self.h_file.write(f"#define {self.c_file.name.upper().split('.')[0]}_H\n")
        self.h_file.write(f"// Header (.h) for font: {self._get_friendly_name()}\n\n")
        self.h_file.write("extern const int TALLEST_CHAR_PIXELS;\n\n")
        self.h_file.write(
            f"extern const unsigned char {self._get_safe_name()}_pixels[];\n\n"
        )
        self.h_file.write("struct font_char {\n")
        self.h_file.write("{}int offset;\n".format(TAB_STR))
        self.h_file.write("{}int w;\n".format(TAB_STR))
        self.h_file.write("{}int h;\n".format(TAB_STR))
        self.h_file.write("{}int left;\n".format(TAB_STR))
        self.h_file.write("{}int top;\n".format(TAB_STR))
        self.h_file.write("{}int advance;\n".format(TAB_STR))
        self.h_file.write("};\n\n")
        self.h_file.write(
            f"extern const struct font_char {self._get_safe_name()}_lookup[];\n\n"
        )
        self.h_file.write(f"#endif // !{self.c_file.name.upper().split('.')[0]}_H")

    def generate_c_source(self):
        self.c_file.write(f"// Source (.c) for font: {self._get_friendly_name()}\n\n")
        self.c_file.write('#include "{}"\n\n'.format(self._get_header_name()))
        self.c_file.write(
            f"const int TALLEST_CHAR_PIXELS = {self._get_height_of_tallest_character()};\n\n"
        )
        self._generate_lookup_table()
        self._generate_pixel_table()

    def _generate_lookup_table(self):
        self.c_file.write(
            f"const struct font_char {self._get_safe_name()}_lookup[] = {{\n"
        )
        if DEBUG:
            self.c_file.write(
                f"{TAB_STR}// offset, width, height, left, top, advance\n"
            )
        offset = 0
        for j in range(128):
            if j in range(ord(FIRST_CHAR), ord(LAST_CHAR) + 1):
                char = chr(j)
                char_bmp, buf, w, h, left, top, advance, pitch = self._get_char(char)
                self._generate_lookup_entry_for_char(
                    char, offset, w, h, left, top, advance
                )
                offset += w * h
            else:
                self.c_file.write("{}{{0, 0, 0, 0, 0}},\n".format(TAB_STR))
        self.c_file.write("{}{{0, 0, 0, 0, 0}}\n".format(TAB_STR))
        self.c_file.write("};\n\n")

    def _generate_lookup_entry_for_char(self, char, offset, w, h, left, top, advance):
        if DEBUG:
            self.c_file.write(
                "{}{{{}, {}, {}, {}, {}, {}}}, // {} ({})\n".format(
                    TAB_STR, offset, w, h, left, top, advance, char, ord(char)
                )
            )
        else:
            self.c_file.write(
                "{}{{{}, {}, {}, {}, {}, {}}},\n".format(
                    TAB_STR, offset, w, h, left, top, advance
                )
            )

    def _generate_pixel_table(self):
        self.c_file.write(
            "const unsigned char {}_pixels[] = {{\n".format(self._get_safe_name())
        )
        if DEBUG:
            self.c_file.write(
                "{}// width, height, left, top, advance\n".format(TAB_STR)
            )
        for i in range(ord(FIRST_CHAR), ord(LAST_CHAR) + 1):
            char = chr(i)
            self._generate_pixel_table_for_char(char)
        self.c_file.write("{}0x00\n".format(TAB_STR))
        self.c_file.write("};\n\n")

    def _generate_pixel_table_for_char(self, char):
        char_bmp, buf, w, h, left, top, advance, pitch = self._get_char(char)
        if DEBUG:
            self.c_file.write("{}// {} ({})\n".format(TAB_STR, char, ord(char)))
        if not buf:
            return ""
        for y in range(char_bmp.rows):
            self.c_file.write("{}".format(TAB_STR))
            self._hex_line(buf, y, w, pitch)
            if DEBUG:
                self.c_file.write(" // ")
                self._ascii_art_line(buf, y, w, pitch)
            self.c_file.write("\n")

    def _get_height_of_tallest_character(self):
        tallest = 0
        for i in range(ord(FIRST_CHAR), ord(LAST_CHAR) + 1):
            char = chr(i)
            char_bmp, buf, w, h, left, top, advance, pitch = self._get_char(char)
            if top - h > tallest:
                tallest = top - h
        return tallest

    def _get_char(self, char):
        char_bmp = self._render_char(char)  # Side effect: updates self.face.glyph
        assert char_bmp.pixel_mode == 2  # 2 = FT_PIXEL_MODE_GRAY
        assert char_bmp.num_grays == 256  # 256 = 1 byte per pixel
        w, h = char_bmp.width, char_bmp.rows
        left = self.face.glyph.bitmap_left
        top = self.pixel_size - self.face.glyph.bitmap_top
        advance = self.face.glyph.linearHoriAdvance >> 16
        buf = char_bmp.buffer  # very slow (which is misleading)
        return char_bmp, buf, w, h, left, top, advance, char_bmp.pitch

    def generate_c_source_for_line(self, char):
        pass

    def _render_char(self, char):
        self.face.load_char(char, freetype.FT_LOAD_RENDER)
        return self.face.glyph.bitmap

    def _hex_line(self, buf, y, w, pitch):
        for x in range(w):
            v = buf[x + y * pitch]
            self.c_file.write("0x{:02x},".format(v))

    def _ascii_art_line(self, buf, y, w, pitch):
        for x in range(w):
            v: int = buf[x + y * pitch]
            self.c_file.write(" .:-=+*#%@"[math.floor(v / 26)])

    def _get_header_name(self):
        return "{}.h".format(self._get_safe_name())

    def _get_source_name(self):
        return "{}.c".format(self._get_safe_name())

    def _get_safe_name(self):
        return "{}_font".format(
            re.sub(r"[^\w\d]+", "_", self._get_friendly_name().lower())
        )

    def _get_friendly_name(self):
        return "{} {} {}".format(
            self.face.family_name, self.face.style_name, self.pixel_size
        )


if __name__ == "__main__":
    main()
