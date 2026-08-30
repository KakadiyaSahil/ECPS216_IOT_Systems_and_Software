""" 
Name: Sahil Mukeshbhai Kakadiya
Profile: Master's Student
UCI Student ID: 93282494
University: University of California, Irvine (UCI)
Course: The Professional Master of Embedded and Cyber-Physical Systems
Major: Computer Engineering
Subject Name: ECPS 216 - F'24: IoT Systems & Software
Assignment Name: Programming Assignment 3 Programming Assignment 3 - All for One, and One for All
                 create a swarm to connect at most three ESP8266's and a Raspberry Pi (as a data logger)
*/
"""
#  -----------------   Start of the Assignment ------------------

import os
import subprocess
import socket
import time
from enum import Enum
from gpiozero import LED, Button
from signal import pause
from threading import Timer, Lock

# Status Enum for the system states
# This Enum class is used to track the different states the system can be in, such as IDLE, WIFI_CONNECTED, etc.
class STATUS(Enum):
    IDLE = 1
    WIFI_CONNECTED = 2
    SEARCHING_AND_COMMUNICATING = 3
    START = 4
    STOP = 5


class SystemController:
    # Define GPIO pin numbers for the LEDs and Button
    LED_WHITE_PIN = 23   # White LED indicates activity
    LED_RED_PIN = 24     
    LED_GREEN_PIN = 20  
    LED_YELLOW_PIN = 25  
    INPUT_BUTTON_PIN = 16 # Button for user interaction
    
    LDR_RAW_MIN = 0         # Minimum LDR sensor raw value
    LDR_RAW_MAX = 1023      # Maximum LDR sensor raw value
    FLASHING_FREQUENCY_MIN = 0.1  # Minimum flashing frequency 
    FLASHING_FREQUENCY_MAX = 1  # Maximum flashing frequency 
    # Timer intervals for online indicator 
    ONLINE_INDICATION_TIMER = 10  

    # Define the target Broadcast IP and port to communicate over UDP
    Broadcast_ip = '255.255.255.255'  
    Broadcast_port = 54321          
    RASP_Device_Token_ID = "RaspBerry_PI_5"  # Unique identifier for the Raspberry Pi in messages

    LED_MAPPING_DICT = {"RED":None,"YELLOW":None, "GREEN":None}
    def __init__(self):
        # Initialize LEDs and button using gpiozero
        self.wled = LED(self.LED_WHITE_PIN)    # White LED
        self.rled = LED(self.LED_RED_PIN)      # Red LED
        self.gled = LED(self.LED_GREEN_PIN)    # Green LED
        self.yled = LED(self.LED_YELLOW_PIN)   # Yellow LED
        self.button = Button(self.INPUT_BUTTON_PIN)  # Button for user input
        self.flashingRateValue =0
        self.flashingcolor = None
        # Initial state of the system is set to IDLE
        self.process_stage = STATUS.IDLE
        self.sock = None  # UDP socket will be initialized later
        self.lock = Lock()  # Thread lock to ensure thread-safe state changes

        # Define the button press event handler
        self.button.when_pressed = self.on_button_press

        # Reset all LEDs to off state initially
        self.reset_leds()

    # Turns off all LEDs to indicate the system is in a neutral state
    def reset_leds(self):
        self.wled.off()
        self.rled.off()
        self.gled.off()
        self.yled.off()
        for key in self.LED_MAPPING_DICT:
            key = None


    # Check whether the device is connected to Wi-Fi by attempting to connect to Google's public DNS server
    def check_wifi(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=5)  # DNS check with a timeout
            print("Connected to Wi-Fi.")
            return True
        except OSError:
            print("Not connected to Wi-Fi.")
            return False

    # If the device is not connected to Wi-Fi, attempt to reconnect by reconfiguring the Wi-Fi settings
    def reconnect_wifi(self):
        print("Attempting to reconnect to Wi-Fi...")
        os.system("sudo wpa_cli -i wlan0 reconfigure")  # Reconfigure Wi-Fi using wpa_cli command
        time.sleep(10)  # Wait 10 seconds for the Wi-Fi to reconnect

    # Initialize the UDP socket for communication with the ESP8266
    def initialize_socket(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.sock.bind((self.Broadcast_ip, self.Broadcast_port))
            print("Socket initialized successfully.")
            self.sock.settimeout(100)  # Set a timeout for receiving data
            return True
        except Exception as e:
            print(f"Error initializing socket: {e}")
            return False

    # Deactivate the socket by closing it when the system stops
    def deactivate_socket(self):
        try:
            if self.sock:
                self.sock.close()  # Close the socket to free up resources
                print("Socket closed successfully.")
            return True
        except Exception as e:
            print(f"Error closing socket: {e}")
            return False

    # Send a UDP message to the ESP8266 with a given message string
    def send_udp_message(self, message):
        try:
            self.sock.sendto(message.encode(), (self.Broadcast_ip, self.Broadcast_port))  # Send message to the Broadcast channel
            print(f"Sent UDP message: {message}")
            return True
        except Exception as e:
            print(f"Error sending UDP message: {e}")
            return False

    # Receive sensor data from the ESP8266 via UDP
    def receive_sensor_data(self):
        try:
            sensordata, addr = self.sock.recvfrom(1024)  # Receive up to 1024 bytes of data
            # print(f"Received sensor data from {addr}: {sensordata.decode()}")
            return sensordata.decode()  # Decode the sensor data to string
        except socket.timeout:
            print("Sensor data receive timed out.")
            self.flashingcolor = None
            self.wled.off()
            self.rled.off()
            self.gled.off()
            self.yled.off()
            Timer(self.flashingRateValue, self.blinkYELLOW).cancel() 
            Timer(self.flashingRateValue, self.blinkGREEN).cancel() 
            Timer(self.flashingRateValue, self.blinkRED).cancel() 
            return None

    # Send a "ONLINE" message to the ESP8266 to initiate synchronization
    def start_handshake(self):
        message = f"{self.RASP_Device_Token_ID}@{self.RASP_Device_Token_ID}@ONLINE@"  # Format the start handshake message
        status = False
        if((self.process_stage == STATUS.SEARCHING_AND_COMMUNICATING) or (self.process_stage == STATUS.START)):
            status = self.send_udp_message(message)
            Timer(self.ONLINE_INDICATION_TIMER, self.start_handshake).start() 
        elif(self.process_stage == STATUS.STOP):
            Timer(self.ONLINE_INDICATION_TIMER, self.start_handshake).cancel()  
        return status

    # Send a "RESET" message to the ESP8266 to stop synchronization
    def stop_handshake(self):
        message = f"{self.RASP_Device_Token_ID}@{self.RASP_Device_Token_ID}@RESET@"  # Format the stop handshake message
        return self.send_udp_message(message)

    def map_value(self, x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_max

    def blinkRED(self):
        if(self.flashingcolor == "RED"):
            self.rled.toggle()
            Timer(self.flashingRateValue, self.blinkRED).start() 
    def blinkGREEN(self):
        if(self.flashingcolor == "GREEN"):
            self.gled.toggle()
            Timer(self.flashingRateValue, self.blinkGREEN).start() 
    def blinkYELLOW(self):
        if(self.flashingcolor == "YELLOW"):
            self.yled.toggle()
            Timer(self.flashingRateValue, self.blinkYELLOW).start() 
    def blink(self, LED_key, ldrDATA):

                if((LED_key != None) or (ldrDATA != None)):
                    blinkrate =float(ldrDATA)
                    self.flashingRateValue = self.map_value(blinkrate, self.LDR_RAW_MIN, self.LDR_RAW_MAX, self.FLASHING_FREQUENCY_MIN, self.FLASHING_FREQUENCY_MAX)
                    if(LED_key == "RED"):
                        self.flashingcolor = "RED"
                        print(f" Blinking the {self.flashingcolor} with Freq: {(1/self.flashingRateValue)} and LDR Data:{ldrDATA} ")
                        Timer(self.flashingRateValue, self.blinkGREEN).cancel() 
                        Timer(self.flashingRateValue, self.blinkYELLOW).cancel() 
                        self.gled.off()
                        self.yled.off()
                        Timer(self.flashingRateValue, self.blinkRED).start() 
                    elif(LED_key == "YELLOW"):
                        self.flashingcolor = "YELLOW"
                        print(f" Blinking the  {self.flashingcolor} with Freq: {(1/self.flashingRateValue)} and LDR Data:{ldrDATA} ")
                        Timer(self.flashingRateValue, self.blinkGREEN).cancel() 
                        Timer(self.flashingRateValue, self.blinkRED).cancel() 
                        self.gled.off()
                        self.rled.off()
                        Timer(self.flashingRateValue, self.blinkYELLOW).start() 
                    elif(LED_key == "GREEN"):
                        self.flashingcolor = "GREEN"
                        print(f" Blinking the  {self.flashingcolor} with Freq: {(1/self.flashingRateValue)} and LDR Data:{ldrDATA} ")
                        Timer(self.flashingRateValue, self.blinkRED).cancel() 
                        Timer(self.flashingRateValue, self.blinkYELLOW).cancel() 
                        self.rled.off()
                        self.yled.off()
                        Timer(self.flashingRateValue, self.blinkGREEN).start() 

    # Process the received sensor data and control the LEDs based on the intensity levels
    def handle_sensor_data(self, sensordata):
        separator = "@"
        data = sensordata.split(separator)
        if data[0] == "ESP_8266":
            if(data[1] == "MASTER"):
                status = False
                for key in self.LED_MAPPING_DICT:
                    if(self.LED_MAPPING_DICT[key] ==  data[2]):
                        status = True
                        break
                if(status == False):
                    print(f"Configuring the New MASTER ESP 8266 : {data[2]}")
                    for key in self.LED_MAPPING_DICT:
                        if(self.LED_MAPPING_DICT[key] == None):
                            self.LED_MAPPING_DICT[key] = data[2]; 
                            status = True
                            break      
                if(True):
                    LED_key = None
                    for key in self.LED_MAPPING_DICT:
                        if(self.LED_MAPPING_DICT[key] == data[2]):
                            LED_key = key
                            break
                    print(f"the MASTER ESP 8266 : {data[2]} is configured with the {LED_key}")
                    self.blink(LED_key, data[4] )

                            
    # Handle button press events and change system states accordingly
    def on_button_press(self):
        with self.lock:  # Ensure thread-safe state changes
            print("Button pressed.")
            if self.process_stage == STATUS.WIFI_CONNECTED:
                self.process_stage = STATUS.SEARCHING_AND_COMMUNICATING  # Begin communication
            elif self.process_stage == STATUS.SEARCHING_AND_COMMUNICATING:
                 self.process_stage = STATUS.STOP  # Reset
            elif self.process_stage == STATUS.START:
                self.process_stage = STATUS.STOP  # Stop communication


    # Main loop that controls the state machine of the system
    def run(self):
        while True:
            # IDLE state: Check Wi-Fi connection and transition to WIFI_CONNECTED
            if self.process_stage == STATUS.IDLE:
                while self.process_stage == STATUS.IDLE:
                    if self.check_wifi():
                        self.process_stage = STATUS.WIFI_CONNECTED
                    else:
                        self.reconnect_wifi()  # Reconnect to Wi-Fi if not connected

            # WIFI_CONNECTED state: Waiting for user interaction (button press)
            if self.process_stage == STATUS.WIFI_CONNECTED:
                print("Raspberry is online, waiting for user command (Button pressed ) to start communication.")
                while(self.process_stage == STATUS.WIFI_CONNECTED):
                 time.sleep(1)  # Sleep to avoid busy-waiting

            # SEARCHING_AND_COMMUNICATING state: Check if ESP8266 is reachable and start communication
            if self.process_stage == STATUS.SEARCHING_AND_COMMUNICATING:
                if self.initialize_socket(): # Socket initialize
                    time.sleep(1)
                    if self.start_handshake():  # Try to initiate synchronization handshake
                        time.sleep(1)
                        self.process_stage = STATUS.START  # Transition to START state once communication begins

            # START state: Receive sensor data and handle it
            if self.process_stage == STATUS.START:
                while self.process_stage == STATUS.START:
                    data = self.receive_sensor_data()  # Receive data from ESP8266
                    if data:
                        self.handle_sensor_data(data)  # Handle the received sensor data

            # STOP state: Stop communication and reset the system
            if self.process_stage == STATUS.STOP:
                print("Stopping communication and resetting system.")
                if self.sock != None:
                    self.stop_handshake()  # Send stop handshake to ESP8266
                self.flashingcolor = None
                Timer(self.flashingRateValue, self.blinkRED).cancel() 
                Timer(self.flashingRateValue, self.blinkYELLOW).cancel() 
                Timer(self.flashingRateValue, self.blinkGREEN).cancel() 
                self.reset_leds()  # Reset all LEDs
                self.wled.on()
                time.sleep(3)
                self.wled.off()
                while not self.deactivate_socket(): # Socket deactivate
                    time.sleep(1)
                self.process_stage = STATUS.IDLE  # Transition back to IDLE state



# Run the main program
if __name__ == "__main__":
    controller = SystemController()  # Create an instance of the controller
    controller.run()  # Start the system loop


#  -----------------   end of the Assignment ------------------