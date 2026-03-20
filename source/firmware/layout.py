from machine import Pin, SPI
import spleen8, spleen16
import time
import framebuf
from st7789py import ST7789, BLACK #type: ignore

"""Display initialization and text functions"""

tft_spi = SPI(0, baudrate=62_500_000, polarity=1, phase=1, sck=Pin(2, Pin.OUT), mosi=Pin(3, Pin.OUT))
tft_cs = Pin(5, Pin.OUT)

tft = ST7789(tft_spi, 240, 320, reset=Pin(7, Pin.OUT), dc=Pin(6, Pin.OUT), cs=tft_cs, rotation=3)
tft.init()

def preconvert_font_to_fb(font):
    WIDTH = font.WIDTH
    HEIGHT = font.HEIGHT
    FIRST = font.FIRST
    LAST = font.LAST
    FONT_BYTES = font.font
    bytes_per_row = (WIDTH + 7) // 8

    glyph_fbs = {}
    for code in range(FIRST, LAST):
        index = (code - FIRST) * HEIGHT * bytes_per_row
        glyph_bytes = FONT_BYTES[index:index + HEIGHT * bytes_per_row]
        
        fb = framebuf.FrameBuffer(bytearray(glyph_bytes), WIDTH, HEIGHT, framebuf.MONO_HMSB)
        fb_flip = framebuf.FrameBuffer(bytearray(WIDTH*HEIGHT*2), WIDTH, HEIGHT, framebuf.MONO_HMSB)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if fb.pixel(x, y):
                    fb_flip.pixel(WIDTH-x, y, 1)
        
        glyph_fbs[chr(code)] = fb_flip
    
    return glyph_fbs

def draw_text(text, x, y, glyphs, width=8, height=16, alignment_x=0, alignment_y=0, color=0xFFFF):
    x = x - ((width * len(text)) * alignment_x // 2) 
    y = y - (height * alignment_y // 2)
    dx = x
    for c in text:
        fb = glyphs.get(c)
        for jx in range(width):
            for jy in range(height):
                if fb.pixel(jx, jy):
                    tft.pixel(dx+jx, y+jy, color)

        dx += width

spleen8_glyphs = preconvert_font_to_fb(spleen8)

"""Root elements and layouts"""

class Widget:
    def __init__(self, x, y, width, height, visible=True):
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.visible = visible

    def draw(self):
        pass

    def update(self):
        pass

class Container(Widget):
    def __init__(self, x, y, width, height, padding=0, spacing=0):
        super().__init__(x, y, width, height)

        self.children = []
        self.padding = padding
        self.spacing = spacing

    def add(self, *widgets):
        for widget in widgets:
            self.children.append(widget)

    def layout(self):
        pass

class HBox(Container):
    def layout(self):
        current_x = self.x + self.padding
        for child in self.children:
            child.x = current_x
            child.y = self.y + self.padding

            current_x += child.width + self.spacing

class VBox(Container):
    def layout(self):
        current_y = self.y + self.padding
        for child in self.children:
            child.x = self.x + self.padding
            child.y = current_y

            current_y += child.height + self.spacing

class Grid(Container):
    def __init__(self, x, y, width, height, rows, cols, padding=0, spacing=0):
        super().__init__(x, y, width, height, padding, spacing)

        self.rows = rows
        self.cols = cols

    def layout(self):
        cell_width = (self.width - (2 * self.padding) - (self.cols - 1) * self.spacing) // self.cols
        cell_height = (self.height - (2 * self.padding) - (self.rows - 1) * self.spacing) // self.rows

        for index, child in enumerate(self.children):
            row, col = divmod(index, self.cols)
            child.x = self.padding + (self.spacing + cell_width) * col
            child.y = self.padding + (self.spacing + cell_height) * row
            child.width = cell_width
            child.height = cell_height

class Screen:
    def __init__(self, color=BLACK):
        self.root = None
        self.color = color

    def set_root(self, container):
        self.root = container

    def render(self, fill=False, layout=False):
        if fill:
            tft.fill(self.color)
        if self.root:
            if layout:
                self.root.layout()
            self._draw_widget(self.root)

    def _draw_widget(self, widget):
        if not widget.visible:
            return
        widget.draw()
        if isinstance(widget, Container):
            for child in widget.children:
                self._draw_widget(child)

"""Widget types"""

class Label(Widget):
    def __init__(self, x, y, text, color, alignment_x=0, alignment_y=0):
        super().__init__(x, y, 8*len(text), 16)
        self.text = text
        self.color = color
        self.alignment_x, self.alignment_y = alignment_x, alignment_y

    def draw(self):
        draw_text(self.text, self.x, self.y, spleen8_glyphs, alignment_x=self.alignment_x, alignment_y=self.alignment_y, color=self.color)

class StatusBar(Widget):
    def __init__(self, y, height, text, bg_color, color, alignment_x=0):
        super().__init__(0, y, 320, height)
        self.text = text
        self.bg_color = bg_color
        self.color = color
        self.alignment_x = 0

    def draw(self):
        aligned_x = self.x + self.width * self.alignment_x // 2 + (8 - (8 * self.alignment_x))
        
        tft.fill_rect(0, self.y, 320, self.height, self.bg_color)
        draw_text(self.text, aligned_x, self.y + 16, spleen8_glyphs, alignment_x=0, alignment_y=1, color=self.color)

class Button(Widget):
    def __init__(self, x, y, width, height, text, bg_color, color, border_color=None, centered=True):
        super().__init__(x, y, width, height)
        self.text = text
        self.bg_color = bg_color
        self.text_color = color
        self.border_color = border_color
        self.centered = centered

    def draw(self):
        aligned_x = self.x if self.centered == False else self.x - self.width // 2
        aligned_y = self.y if self.centered == False else self.y - self.height // 2

        tft.fill_rect(aligned_x, aligned_y, self.width, self.height, self.border_color)
        tft.fill_rect(aligned_x + 1, aligned_y + 1, self.width - 2, self.height - 2, self.bg_color)

        draw_text(self.text, aligned_x + self.width // 2, aligned_y + self.height // 2, spleen8_glyphs, alignment_x=1, alignment_y=1, color=self.text_color)

class Spacer(Widget):
    def __init__(self, width=None, height=None):
        super().__init__(0, 0, width or 0, height or 0)

    def draw(self):
        pass