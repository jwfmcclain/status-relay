import time
import board
import busio

import json
import socketpool
import wifi
import ssl

import adafruit_requests

import terminalio
import displayio
from adafruit_progressbar.horizontalprogressbar import (
    HorizontalProgressBar,
    HorizontalFillDirection,
)
from adafruit_display_text import label


# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

for network in wifi.radio.start_scanning_networks():
    print(f"\t{str(network.ssid, "utf-8")} {network.rssi} {network.channel}")

wifi.radio.connect(secrets['ssid'], secrets['password'])
pool = socketpool.SocketPool(wifi.radio)
session = adafruit_requests.Session(pool, ssl.create_default_context())

print(f"Connected to {secrets['ssid']}\nIP: {wifi.radio.ipv4_address}")

# Make the display context
top = displayio.Group()
board.DISPLAY.show(top)

status_line = label.Label(terminalio.FONT, text="", scale=2, color=0xFFFFFF, x=1, y=16)
message_line = label.Label(terminalio.FONT, text="", scale=1, color=0xFFFFFF, x=1, y=36)
progress_bar = HorizontalProgressBar((1, 50), (238, 25),
                                     fill_color=0x000000, outline_color=0xFFFFFF, bar_color=0x13c100,
                                     direction=HorizontalFillDirection.LEFT_TO_RIGHT)
time_bar = HorizontalProgressBar((1, 50+25), (238, 25),
                                 fill_color=0x000000, outline_color=0xFFFFFF, bar_color=0x13c100,
                                 direction=HorizontalFillDirection.LEFT_TO_RIGHT)
overtime_bar = HorizontalProgressBar((1, 50+25), (238, 25),
                                 fill_color=0xFF0000, outline_color=0xFFFFFF, bar_color=0x13c100,
                                 direction=HorizontalFillDirection.LEFT_TO_RIGHT)
overtime_bar.hidden = True
height_bar = HorizontalProgressBar((1, 50+25*2), (238, 25),
                                  fill_color=0x000000, outline_color=0xFFFFFF, bar_color=0x13c100,
                                  direction=HorizontalFillDirection.LEFT_TO_RIGHT)

top.append(status_line)
top.append(message_line)
top.append(progress_bar)
top.append(time_bar)
top.append(overtime_bar)
top.append(height_bar)

TEXT_URL = "https://i0-5756de2f61bd072920e5f912cd7c1a09.srv.kou.services/"
headers={"Authorization" : f"Bearer {secrets['kou_key']}",
         "accept" : "application/json"}
print("Fetching text from", TEXT_URL)

while True:
    r = session.get(TEXT_URL, headers=headers)
    text = r.text.strip()
    r.close()
    
    status = json.loads(text)
    print(status)

    status_line.text = status['state']
    message_line.text = status['message']

    if 'percent_done' in status and status['percent_done'] is not None:
        progress_bar.value = status['percent_done']
    else:
        progress_bar.value = 0

    if 'estimated_print_time' in status and 'elapsed_print_time' in status:
        elapsed = float(status['elapsed_print_time'])
        expected = status['estimated_print_time']
        if elapsed <= expected:
            print(f"1 {elapsed} {expected}")
            time_bar.hidden = False
            overtime_bar.hidden = True
            time_bar.value = (elapsed / expected) * 100
        else:
            print(f"2 {elapsed} {expected}")
            time_bar.hidden = True
            overtime_bar.hidden = False
            overtime_bar.value = (expected / elapsed) * 100
    else:
        time_bar.hidden = False
        overtime_bar.hidden = True
        time_bar.value = 0

    if 'current_z' in status and 'max_z' in status and status['current_z'] is not None:
        model_height = status['max_z']
        cur_z = status['current_z']
        if cur_z >= model_height:
            height_bar.value = 100
        else:
            height_bar.value = (cur_z / model_height) * 100
    else:
        height_bar.value = 0
        
    time.sleep(60)
print("Done!")
