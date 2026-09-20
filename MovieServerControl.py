import os

from RPLCD.gpio import CharLCD
import RPi.GPIO as GPIO
import psutil
import socket
import time
from datetime import timedelta
import subprocess
import threading
import json

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
stop_event = threading.Event()
data_lock = threading.Lock()
hdd_data = {}
#======================================
#Functions=============================
def MakeLCDLine(left, right):
    return f"{left:<{16 - len(right)}}{right}"
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
    uptime = f"{days:02d}:{hours:02d}:{minutes:02d}"
    return uptime
def GetJellyfinStatus():
    result = subprocess.run(
        ["systemctl", "is-active", "--quiet", "jellyfin"]
    )

    return result.returncode == 0
def UpdateLcd():
    while not stop_event.is_set():
        JellyStatus = "OK" if GetJellyfinStatus() else "ERR"
        Line1 = MakeLCDLine(GetUptime(), JellyStatus)
        Line2 = f"  {GetIP()} "
        CharLCD.write_string(value=Line1)
        CharLCD.cursor_pos = (1, 0)
        CharLCD.write_string(value=Line2)
        CharLCD.cursor_pos = (0, 0)
        stop_event.wait(60)
def get_smart_temperature(device):
    try:
        result = subprocess.run(
            [
                "smartctl",
                "-A",
                device,
                "-d",
                "sat",
                "-j"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        return data.get(
            "temperature",
            {}
        ).get(
            "current"
        )
    except Exception as e:
        print(
            f"SMART error {device}: {e}"
        )
        return None
def get_cpu_temperature():
    try:
        result = subprocess.run(
            [
                "vcgencmd",
                "measure_temp"
            ],
            capture_output=True,
            text=True
        )
        temp = (
            result.stdout
            .split("=")[1]
            .split("'")[0]
        )
        return float(temp)
    except Exception:
        return None
def get_physical_disks():
    result = subprocess.run(
        [
            "lsblk",
            "-J",
            "-o",
            "NAME,TYPE,TRAN,ROTA,MODEL,SIZE"
        ],
        capture_output=True,
        text=True
    )
    data = json.loads(result.stdout)
    drives = []
    for disk in data["blockdevices"]:
        # Only SATA disks
        if (
            disk["type"] == "disk"
            and disk.get("tran") == "sata" or "usb"
        ):
            drives.append({
                "device": "/dev/" + disk["name"],
                "model": disk.get("model"),
                "size": disk.get("size")
            })
    return drives
def FanControl():
    while not stop_event.is_set():
        drives = get_physical_disks()
        TempList = []
        for drive in drives:
            device = drive["device"]
            TempList.append(get_smart_temperature(device))
        TempList.append(get_cpu_temperature())
        print(TempList)
        print(drives)
        stop_event.wait(5)
#======================================
if __name__ == "__main__":


    threads = [
        threading.Thread(
            target=UpdateLcd,
            daemon=True
        ),
        threading.Thread(
            target=FanControl,
            daemon=True
        )
    ]


    for t in threads:
        t.start()


    try:

        while True:
            time.sleep(1)


    except KeyboardInterrupt:

        print("Stopping...")

        stop_event.set()

        for t in threads:
            t.join()

GPIO.cleanup()