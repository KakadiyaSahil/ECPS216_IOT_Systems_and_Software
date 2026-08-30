""" 
Name: Sahil Mukeshbhai Kakadiya
Profile: Master's Student
UCI Student ID: 93282494
University: University of California, Irvine (UCI)
Course: The Professional Master of Embedded and Cyber-Physical Systems
Major: Computer Engineering
Subject Name: ECPS 216 - F'24: IoT Systems & Software
Assignment Name: Programming Assignment 2 (Final version) - UDP Protocol Implementaed
({Raspberry Pi and 1 ESP8266 Swarm Communication Using LED Indicators and Light Sensors)

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
    ERROR = 6



class SystemController:
    # Define GPIO pin numbers for the LEDs and Button
    LED_WHITE_PIN = 23   # White LED indicates errors or activity
    LED_RED_PIN = 24     
    LED_GREEN_PIN = 20  
    LED_YELLOW_PIN = 25  
    INPUT_BUTTON_PIN = 16 # Button for user interaction

    # Intensity levels for sensor data
    LOW_INTENSITY_LEVEL_MIN = 0
    LOW_INTENSITY_LEVEL_MAX = 500
    MEDIUM_INTENSITY_LEVEL_MIN = 501
    MEDIUM_INTENSITY_LEVEL_MAX = 800
    HIGH_INTENSITY_LEVEL_MIN = 801
    HIGH_INTENSITY_LEVEL_MAX = 1023

    # Timer intervals for error LED blinking
    ERROR_INDICATION_TIMER = 0.5  # Time in seconds to toggle white LED in case of errors

    # Define the target ESP8266 IP and port to communicate over UDP
    ESP_target_ip = '192.168.137.179'  # Update with the actual ESP8266 IP address
    ESP_target_port = 54321          # Port number used for UDP communication
    RASP_Device_Token_ID = "RaspBerry_PI_5"  # Unique identifier for the Raspberry Pi in messages

    def __init__(self):
        # Initialize LEDs and button using gpiozero
        self.wled = LED(self.LED_WHITE_PIN)    # White LED
        self.rled = LED(self.LED_RED_PIN)      # Red LED
        self.gled = LED(self.LED_GREEN_PIN)    # Green LED
        self.yled = LED(self.LED_YELLOW_PIN)   # Yellow LED
        self.button = Button(self.INPUT_BUTTON_PIN)  # Button for user input

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
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create a UDP socket
            print("Socket initialized successfully.")
            self.sock.settimeout(10)  # Set a timeout for receiving data
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
            self.sock.sendto(message.encode(), (self.ESP_target_ip, self.ESP_target_port))  # Send message to the ESP
            print(f"Sent UDP message: {message}")
            return True
        except Exception as e:
            print(f"Error sending UDP message: {e}")
            return False

    # Receive sensor data from the ESP8266 via UDP
    def receive_sensor_data(self):
        try:
            sensordata, addr = self.sock.recvfrom(1024)  # Receive up to 1024 bytes of data
            print(f"Received sensor data from {addr}: {sensordata.decode()}")
            return sensordata.decode()  # Decode the sensor data to string
        except socket.timeout:
            print("Sensor data receive timed out.")
            return None

    # Check if the ESP8266 IP address is reachable by sending a ping request
    def is_ip_reachable(self):
        try:
            result = subprocess.run(["ping", "-c", "1", self.ESP_target_ip], stdout=subprocess.PIPE)  # Ping once
            if result.returncode == 0:
                print(f"IP {self.ESP_target_ip} is reachable.")
                return True
            else:
                print(f"IP {self.ESP_target_ip} is not reachable.")
                return False
        except Exception as e:
            print(f"Error checking IP reachability: {e}")
            return False

    # Send a "START_SYNC" message to the ESP8266 to initiate synchronization
    def start_handshake(self):
        message = f"{self.RASP_Device_Token_ID}@START_SYNC@"  # Format the start handshake message
        return self.send_udp_message(message)

    # Send a "STOP_SYNC" message to the ESP8266 to stop synchronization
    def stop_handshake(self):
        message = f"{self.RASP_Device_Token_ID}@STOP_SYNC@"  # Format the stop handshake message
        return self.send_udp_message(message)

    # Process the received sensor data and control the LEDs based on the intensity levels
    def handle_sensor_data(self, sensordata):
        sensordata = float(sensordata)  # Convert sensor data from string to float
        # Low intensity: Turn on only the green LED
        if self.LOW_INTENSITY_LEVEL_MIN <= sensordata <= self.LOW_INTENSITY_LEVEL_MAX:
            print("Low intensity - Green LED")
            self.gled.on()
            self.rled.off()
            self.yled.off()
        # Medium intensity: Turn on both green and yellow LEDs
        elif self.MEDIUM_INTENSITY_LEVEL_MIN <= sensordata <= self.MEDIUM_INTENSITY_LEVEL_MAX:
            print("Medium intensity - Green and Yellow LEDs")
            self.gled.on()
            self.yled.on()
            self.rled.off()
        # High intensity: Turn on all LEDs (green, yellow, and red)
        elif self.HIGH_INTENSITY_LEVEL_MIN <= sensordata <= self.HIGH_INTENSITY_LEVEL_MAX:
            print("High intensity - All LEDs")
            self.gled.on()
            self.yled.on()
            self.rled.on()

    # Handle button press events and change system states accordingly
    def on_button_press(self):
        with self.lock:  # Ensure thread-safe state changes
            print("Button pressed.")
            if self.process_stage == STATUS.WIFI_CONNECTED:
                self.process_stage = STATUS.SEARCHING_AND_COMMUNICATING  # Begin communication
            elif self.process_stage == STATUS.SEARCHING_AND_COMMUNICATING:
                 self.process_stage = STATUS.STOP  # Reset on error
            elif self.process_stage == STATUS.START:
                self.process_stage = STATUS.STOP  # Stop communication
            elif self.process_stage == STATUS.ERROR:
                self.process_stage = STATUS.STOP  # Reset on error

    # Toggle the white LED to indicate an error has occurred
    def error_indication_action(self):
        self.wled.toggle()  # Blink the white LED
        if(self.process_stage == STATUS.ERROR):
            Timer(self.ERROR_INDICATION_TIMER, self.error_indication_action).start()  # Set a timer for the next toggle
        elif(self.process_stage == STATUS.STOP):
            self.wled.off()
            Timer(self.ERROR_INDICATION_TIMER, self.error_indication_action).cancel()  # reset a timer for the next toggle (no need to toggle, it is going to the stop  state)

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
                self.wled.on()  # Turn on white LED while searching
                if self.is_ip_reachable():  # checks until the ESP8266 is reachable
                    if self.initialize_socket(): # Socket initialize
                        time.sleep(1)
                        if self.start_handshake():  # Try to initiate synchronization handshake
                            time.sleep(1)
                            self.process_stage = STATUS.START  # Transition to START state once communication begins

            # START state: Receive sensor data and handle it, or transition to ERROR on failure
            if self.process_stage == STATUS.START:
                print("Now the Handshake is doen, ESP should response the Sensor DATA in 10 sec otherwise Raspberry detects it as error.")
                while self.process_stage == STATUS.START:
                    data = self.receive_sensor_data()  # Receive data from ESP8266
                    if data:
                        self.handle_sensor_data(data)  # Handle the received sensor data
                    else:
                        self.process_stage = STATUS.ERROR  # Transition to ERROR if data reception fails

            # STOP state: Stop communication and reset the system
            if self.process_stage == STATUS.STOP:
                print("Stopping communication and resetting system.")
                if self.sock != None:
                    self.stop_handshake()  # Send stop handshake to ESP8266
                self.reset_leds()  # Reset all LEDs

                while not self.deactivate_socket(): # Socket deactivate
                    time.sleep(1)
                self.process_stage = STATUS.IDLE  # Transition back to IDLE state

            # ERROR state: Indicate the error by blinking the white LED
            if self.process_stage == STATUS.ERROR:
                print("Error occurred. Indicating with white LED.")
                self.error_indication_action()  # Blink the white LED to indicate an error
                print("stays in (Error state) untill the user do not press the button to re-insiate the communication")
                while(self.process_stage == STATUS.ERROR): #stays untill the user do not press the button to re-insiate the communication
                    time.sleep(1)


# Run the main program
if __name__ == "__main__":
    controller = SystemController()  # Create an instance of the controller
    controller.run()  # Start the system loop


#  -----------------   end of the Assignment ------------------