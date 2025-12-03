#include "font_out.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

const int WIDTH = 800;
const int HEIGHT = 150;
const int TRANSPARENT_COLOR = 0;

void draw_text(uint8_t *buf, int pos_x, int pos_y, char *s);
int text_width(char *s);
void draw_text_centered(uint8_t *buf, int pos_y, char *s);
void draw_text_right_adjusted(uint8_t *buf, int pos_y, char *s);
void write_ppm(char *filename, uint8_t *buf);

int main(void) {
  uint8_t *buf = malloc(WIDTH * HEIGHT * sizeof(uint8_t));
  draw_text(buf, 0, 0 * TALLEST_CHAR_PIXELS,
            "That which does not kill me makes me stronger");
  draw_text_centered(buf, 1 * TALLEST_CHAR_PIXELS,
                     "That which does not kill me makes me stronger");
  draw_text_right_adjusted(buf, 2 * TALLEST_CHAR_PIXELS,
                           "That which does not kill me makes me stronger");
  draw_text_centered(buf, 3 * TALLEST_CHAR_PIXELS,
                     "1234567890 !@#$%^&*()-=_+~';:?></.,");
  write_ppm("text_sample.ppm", buf);
  return 0;
}

void draw_text(uint8_t *buf, int pos_x, int pos_y, char *s) {
  char c = *s;
  while (c) {
    const struct font_char font_c = font_lookup[c];
    for (int y = 0; y < font_c.h; ++y) {
      for (int x = 0; x < font_c.w; ++x) {
        uint8_t v = font_pixels[font_c.offset + x + y * font_c.w];
        if (v != TRANSPARENT_COLOR) {
          buf[pos_x + x + font_c.left + (pos_y + y + font_c.top) * WIDTH] = v;
        }
      }
    }
    pos_x += font_c.advance;
    c = *(++s);
  }
}

int text_width(char *s) {
  char c = *s;
  int w = 0;
  while (c) {
    const struct font_char font_c = font_lookup[c];
    w += font_c.advance;
    c = *(++s);
  }
  return w;
}

void draw_text_centered(uint8_t *buf, int pos_y, char *s) {
  int x = WIDTH / 2 - text_width(s) / 2;
  draw_text(buf, x, pos_y, s);
}

void draw_text_right_adjusted(uint8_t *buf, int pos_y, char *s) {
  int x = WIDTH - text_width(s);
  draw_text(buf, x, pos_y, s);
}

void write_ppm(char *filename, uint8_t *buf) {
  FILE *fp = fopen(filename, "wb");
  fprintf(fp, "P6\n%d %d 255\n", WIDTH, HEIGHT);
  for (int y = 0; y < HEIGHT; ++y) {
    for (int x = 0; x < WIDTH; ++x) {
      uint8_t v = buf[x + (y * WIDTH)];
      fwrite(&v, 1, 1, fp);
      fwrite(&v, 1, 1, fp);
      fwrite(&v, 1, 1, fp);
    }
  }
}
