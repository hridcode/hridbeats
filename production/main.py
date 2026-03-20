from machine import Pin, PWM, SPI, ADC
from sdcard import SDCard
import spleen8, spleen16
import layout
import time, os
import framebuf
from st7789py import color565, WHITE, YELLOW

joystick_x, joystick_y = ADC(Pin(27)), ADC(Pin(28))
joystick_sw = Pin(15, pull=Pin.PULL_UP)

pot = ADC(Pin(26))
pot_left, pot_right = Pin(8, pull=Pin.PULL_UP), Pin(9, pull=Pin.PULL_UP)

rotary_l, rotary_r = Pin(11), Pin(12)
rotary_push = Pin(13, pull=Pin.PULL_UP)

int_button = Pin(14, pull=Pin.PULL_UP)

sd_spi = SPI(0, sck=Pin(18, Pin.OUT), mosi=Pin(19, Pin.OUT), miso=Pin(16))
sd_cs = Pin(17, Pin.OUT)

sd = SDCard(sd_spi, sd_cs)

vfs = os.VfsFat(sd) # type: ignore

os.mount(vfs, "/sd")
print("Filesystem check")
print(os.listdir("/sd"))

BG_COLOR = color565(75, 86, 130)
STATUS_BAR_GRAY = color565(80, 80, 80)
BUTTON_GRAY = color565(170, 170, 170)

screen = layout.Screen(BG_COLOR)

home_root = layout.Container(0, 0, 320, 240)
status = layout.StatusBar(0, 32, "Hello world!", STATUS_BAR_GRAY, WHITE)
home_root.add(status)

new_project_button = layout.Button(160, 100, 210, 50, "New Project", BUTTON_GRAY, WHITE, STATUS_BAR_GRAY)
open_project_button = layout.Button(160, 172, 210, 50, "Open Project", BUTTON_GRAY, WHITE, STATUS_BAR_GRAY)
home_root.add(new_project_button, open_project_button)

screen.set_root(home_root)

screen.render(fill=True, layout=True)