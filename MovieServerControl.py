import Adafruit_CharLCD as LCD
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
rs = 23
e = 24
d4 = 4
d5 = 17
d6 = 27
d7 = 22
fan = 12

lcd_columns = 16
lcd_rows = 2

lcd = LCD.Adafruit_CharLCD(rs, e, d4, d5, d6, d7, lcd_columns, lcd_rows)

lcd.message("Works")
time.sleep(5)

GPIO.cleanup()