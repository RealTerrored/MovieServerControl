import os
import warnings
from os import wait

from RPLCD.gpio import CharLCD
import RPi.GPIO as GPIO
import psutil
import socket
import time
from datetime import timedelta
import subprocess
import threading
import json
import signal

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
GPIO.setmode(GPIO.BCM)
GPIO.setup(fan, GPIO.OUT)
fan_pwm = GPIO.PWM(fan, 25000)  # 25 kHz
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
        lcd.write_string(value=Line1)
        lcd.cursor_pos = (1, 0)
        lcd.write_string(value=Line2)
        lcd.cursor_pos = (0, 0)
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
        if disk["type"] == "disk" and disk.get("tran") in ("usb", "sata"):
            drives.append({
                "device": "/dev/" + disk["name"],
                "model": disk.get("model"),
                "size": disk.get("size"),
                "rotational": disk.get("rota")
            })
    return drives
def FanControl():
    print("FanControl thread started", flush=True)
    while not stop_event.is_set():
        drives = get_physical_disks()
        TempList = []
        for drive in drives:
            device = drive["device"]
            TempList.append(get_smart_temperature(device))
        TempList.append(get_cpu_temperature())
        fanspeed = temp_to_percent(max(TempList), 0, 80, 30)
        print(str(fanspeed) + " " + str(max(TempList)), flush=True)
        fan_pwm.ChangeDutyCycle(fanspeed)
        stop_event.wait(5)
def shutdown(signum, frame):
    print("Stopping...")
    stop_event.set()
def temp_to_percent(current, min_temp, max_temp, min_threshold):
    value = clamp(((current - min_temp) / (max_temp - min_temp) * 100), 0, 100)
    if value < min_threshold:
        return 0
    else:
        return value
def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))
#======================================
fan_pwm.start(100)
lcd.write_string("Server starting...")
lcd.cursor_pos = (0, 0)
time.sleep(5)
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

    print("Starting threads...", flush=True)
    for t in threads:
        t.start()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    stop_event.wait()
    for t in threads:
        t.join()
    lcd.clear()
    GPIO.cleanup()