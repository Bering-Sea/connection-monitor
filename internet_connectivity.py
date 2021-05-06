# My version of this app. 
# any comments that are made starting off with *** are my comments. 
import datetime
import os
import signal
import socket
import sys
import time
from smbus2 import SMBus # *** this one is important. You need to put from smbus2 and capitalize the SMB in import SMBus.

# *** I copied the example relay.py from wiki.52pi.com/index.php/DockerPi_4_Channel_Relay_SKU:_EP-0099#Customer_Application site.
# *** It did not work for me when i tested it out. I had to some research and you'll notice some of the changes i made. 

DEVICE_BUS = 1 # *** this from the wiki.52pi.com site. 
DEVICE_ADDR = 0x10 # *** this address is with the switches both down. 
bus = SMBus(DEVICE_BUS) # *** this is modified from the 52.pi site. I deleted some wording to make this work.

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
            # *** Here is where I added code to make the relay turn on and off. 
            print("The internet is on")
            bus.write_byte_data(DEVICE_ADDR, 1, 0xFF)
            # *** Notice the number 1? that means its using relay 1
            time.sleep(1)
            bus.write_byte_data(DEVICE_ADDR, 1, 0x00)
            time.sleep(1)
            bus.write_byte_data(DEVICE_ADDR, 2, 0xFF)
            # *** obviously using relay 2. You can change any of these numbers or use 1 or all 4 relays.
            time.sleep(1)
            bus.write_byte_data(DEVICE_ADDR, 2, 0x00)
            time.sleep(1)
            time.sleep(interval)
            # *** relay 1 and 2 will turn on and off while the internet on.
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
                # *** Another spot I changed the code. This uses relay 3 and 4 as you can see. 
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
                # *** relay 3 and 4 will turn on and off while the internet is down. 
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
