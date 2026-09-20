import os

from RPLCD.gpio import CharLCD
import RPi.GPIO as GPIO
import psutil
import socket
import time
from datetime import timedelta
import subprocess

GPIO.setmode(GPIO.BCM)
#Variables=============================
rs = 23
e = 24
d4 = 4
d5 = 17
d6 = 27
d7 = 22
fan = 12
lcd_columns = 16
lcd_rows = 2
lcd = CharLCD(numbering_mode=GPIO.BCM, pin_rs=rs, pin_e=e, pins_data=[d4, d5, d6, d7], cols=lcd_columns, rows=lcd_rows)
#======================================
#Functions=============================
def GetIP():
    addresses = psutil.net_if_addrs().get("eth0", [])

    for address in addresses:
        if address.family == socket.AF_INET:
            return address.address

    return "No IP"
def GetUptime():
    delta = timedelta(seconds=(time.time() - psutil.boot_time()))
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime = f"{days:02d}:{hours:02d}:{minutes:02d}:{seconds:02d}"
    return uptime
def GetJellyfinStatus():
    result = subprocess.run(
        ["systemctl", "is-active", "--quiet", "jellyfin"]
    )

    return result.returncode == 0
#======================================
print(GetIP())
print(GetUptime())
print(GetJellyfinStatus())

GPIO.cleanup()