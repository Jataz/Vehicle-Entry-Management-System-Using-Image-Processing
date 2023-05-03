
from serial import Serial
from time import sleep
from threading import Thread


def print_to_arduino(string):
   arduino.write(bytes(f"{string};", 'utf-8'))

def open_gate():
   print_to_arduino('open')

def close_gate():
   print_to_arduino("close")


# Serial communication setup
arduino = Serial("COM3", 9600)

def open_and_close_gate_thread_func():
   open_gate()
   sleep(5)
   close_gate()

def open_and_close_gate():
   thread = Thread(target=open_and_close_gate_thread_func)
   thread.start()
   
   
   #updat the last frame
   #serial communication between the machine and the arduino