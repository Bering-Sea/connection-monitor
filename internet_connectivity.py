import datetime
import os
import signal
import socket
import sys
import time
from smbus2 import SMBus

DEVICE_BUS = 1
DEVICE_ADDR = 0x10
bus = SMBus(DEVICE_BUS)

def internet(host = "8.8.8.8", port = 53, timeout = 4):
    '''
    Tests connection by pinging Google Public DNS

    -> return True if host is reachable, False if it times out
    '''
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
    except OSError as error:
        return False
    else:
        s.close()
        return True


def exit_program(signal_received, frame):
    # Handles ctrl + c from user and logs the end of the monitoring session.
    program_end = datetime.datetime.now()
    end_message = ("Connection monitoring session terminated succesfully at: " + str(program_end) + 
                   "\n----------------------------------------------------------------------------------------\n\n\n")
    with open("connection_log.log", "a") as writer:
        writer.write(end_message)
    print("Session exited succesfully. \n")
    sys.exit()
    

def calculate_outage_duration(timeout, timebackon):
    return timebackon - timeout
    # TESTING SIMPLE DATEOBJECT SUBTRACTION
    # return time.strftime('%H:%M:%S', time.gmtime())


def perpetual_connection_monitor(interval):
    '''
    checks internet() every 'interval' seconds
    '''
    # Logs the time at which the program begins monitoring.
    print("\nMonitoring your connection. Press ctrl+c to exit the session.\n")
    program_start = datetime.datetime.now()
    starttime = str(program_start)
    with open("connection_log.log", "a") as writer:
        writer.write("----------------------------------------------------------------------------------------\n")
        writer.write("Connection monitoring session start time: " + starttime + "\n")

    # Allows user to exit with ctrl + c and log the program's end time.
    signal.signal(signal.SIGINT, exit_program)

    while True:
        if internet():
            print("The internet is on")
            bus.write_byte_data(DEVICE_ADDR, 1, 0xFF)
            time.sleep(1)
            bus.write_byte_data(DEVICE_ADDR, 1, 0x00)
            time.sleep(1)
            bus.write_byte_data(DEVICE_ADDR, 2, 0xFF)
            time.sleep(1)
            bus.write_byte_data(DEVICE_ADDR, 2, 0x00)
            time.sleep(1)
            time.sleep(interval)
        else:
            total_downtime_seconds = 0
            downtime_start = datetime.datetime.now()
            # Log the time at which connection was lost.
            with open("connection_log.log", "a") as writer:
                writer.write("---\n")
                message = "Offline as of: " + str(downtime_start) + "\n"
                writer.write(message)

            # Check every 'interval' seconds to see if the connection is back. Sum up the outage time in seconds by adding 'interval' to the total. 
            while not internet():
                print("Lost connection, trying to reconnect.")
                bus.write_byte_data(DEVICE_ADDR, 3, 0xFF)
                time.sleep(1)
                bus.write_byte_data(DEVICE_ADDR, 3, 0x00)
                time.sleep(1)
                bus.write_byte_data(DEVICE_ADDR, 4, 0xFF)
                time.sleep(1)
                bus.write_byte_data(DEVICE_ADDR, 4, 0x00)
                time.sleep(1)
                time.sleep(interval)
                #total_downtime_seconds += interval

            # Log time of first subsequent succesful connection after a period offline:
            back_online = datetime.datetime.now()
            with open("connection_log.log", "a") as writer:
                message = "Connection restored at:" + str(back_online) + "\n"
                writer.write(message)

            # Log the length of the outage
            duration = calculate_outage_duration(downtime_start, back_online)
            with open("connection_log.log", "a") as writer:
                message = "Duration of outage: " + str(duration) + "\n"
                writer.write(message)
                writer.write("---\n")


perpetual_connection_monitor(1)
