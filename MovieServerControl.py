from RPLCD.gpio import CharLCD
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

lcd = CharLCD(numbering_mode=GPIO.BCM, pin_rs=rs, pin_e=e, pins_data=[d4, d5, d6, d7], cols=lcd_columns, rows=lcd_rows)

lcd.write_string("Works")
lcd.cursor_pos = (1, 0)
lcd.write_string("Perfectly")
time.sleep(5)

GPIO.cleanup()