""" 
Name: Sahil Mukeshbhai Kakadiya
Profile: Master's Student
UCI Student ID: 93282494
University: University of California, Irvine (UCI)
Course: The Professional Master of Embedded and Cyber-Physical Systems
Major: Computer Engineering
Subject Name: ECPS 216 - F'24: IoT Systems & Software
Assignment Name: Programming Assignment 4 - The Plot Thickens
*/
"""
#  -----------------   Start of the Assignment ------------------

import os
import socket
import time
from enum import Enum
from gpiozero import LED, Button
import time
from threading import Timer
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from queue import Queue
from datetime import datetime
# # Set the Pin Factory to Mock
# from gpiozero.pins.mock import MockFactory
# from gpiozero import Device
# Device.pin_factory = MockFactory()
# from collections import defaultdict

# Status Enum for the system states
class STATUS(Enum):
    IDLE = 1
    START_VISUALIZATION = 2
    START_COLLECTING = 3
    STOP = 4

class WiFiManager:
    def check_wifi(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            print("Connected to Wi-Fi.")
            return True
        except OSError:
            print("Not connected to Wi-Fi.")
            return False

    def reconnect_wifi(self):
        print("Attempting to reconnect to Wi-Fi...")
        os.system("sudo wpa_cli -i wlan0 reconfigure")
        time.sleep(10)

class SocketManager:
    def __init__(self, broadcast_ip='255.255.255.255', broadcast_port=54321):
        self.sock = None
        self.broadcast_ip = broadcast_ip
        self.broadcast_port = broadcast_port

    def initialize_socket(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.sock.bind((self.broadcast_ip, self.broadcast_port))
            print("Socket initialized successfully.")
            self.sock.settimeout(100)
            return True
        except Exception as e:
            print(f"Error initializing socket: {e}")
            return False

    def deactivate_socket(self):
        try:
            if self.sock:
                self.sock.close()
                print("Socket closed successfully.")
            return True
        except Exception as e:
            print(f"Error closing socket: {e}")
            return False

    def send_udp_message(self, message):
        try:
            self.sock.sendto(message.encode(), (self.broadcast_ip, self.broadcast_port))
            print(f"Sent UDP message: {message}")
            return True
        except Exception as e:
            print(f"Error sending UDP message: {e}")
            return False

    def receive_sensor_data(self):
        try:
            sensordata, addr = self.sock.recvfrom(1024)
            return sensordata.decode(), addr
        except socket.timeout:
            print("Sensor data receive timed out.")
            return None

class Logger: 
    def __init__(self, log_dir="logs", graph_data = None):
        self.log_dir = log_dir
        self.log_file = None
        self.log_filename = None
        self.graph_data = graph_data
        os.makedirs(self.log_dir, exist_ok=True)

    def create_new_log(self):
        if self.log_file:
            self.log_file.close()
        self.log_filename = f"{self.log_dir}/log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        print(f"setting up the log file with the name and path {self.log_filename}")
        self.log_file = open(self.log_filename, "w")
    def write_log(self):
        # Create and open the log file
        if self.log_filename == None:
            return  
        print(f"writing Log summary to {self.log_filename}")
        if (self.log_file != None) & (self.graph_data.master_cumulative_times != None) & (self.graph_data.master_log != None):
         # Extract unique master devices
                unique_masters = {entry["master_device"]: entry["color"] for entry in self.graph_data.master_log}
                unique_masters_pi = {entry["master_device"]: entry["ip_address"] for entry in self.graph_data.master_log}
                self.log_file.write("Summary of Masters:\n")
                self.log_file.write(f"Total Unique Masters: {len(unique_masters)}\n")
                self.log_file.write("\nDetails:\n")
                for master, color in unique_masters.items():
                    Master_name = f"Device ID: {master} \nIP address: {unique_masters_pi[master]}"
                    self.log_file.write(f"Master Device: {master}, IP-Address : {unique_masters_pi[master]}, Color: {color}, Cumulative Time: {self.graph_data.master_cumulative_times[Master_name]:.2f} seconds\n")
                self.log_file.write("\nComplete Log Entries:\n")
                for entry in self.graph_data.master_log:
                    self.log_file.write(str(entry) + "\n")

                print(f"Log summary written to {self.log_filename}")
        else:
            print(f"Log summary is not written to file")

   
    def close_log(self):
        self.write_log()
        if self.log_file:
            self.log_file.close()

class GraphUpdater:
    def __init__(self, master_manager):

        self.Master = master_manager

        # Initialize variables for storing the extracted master data
        self.master_id = None
        self.current_time = None
        self.ip_address = None
        self.port = None
        self.led_attached = None  # This will be used as the color
        self.ldr_value = None
        self.is_master = False

        # Data for the line plot (LDR values) and bar chart (master time tracking)
        self.ldr_data = {}
        self.master_cumulative_times = {}  # Store cumulative time for each master
        self.device_colors = {}  # Store device ID -> color mapping
        self.master_log = []
        self.log_entry_no = 0
        # Set up Matplotlib figure and axes
        self.fig, self.ax1, self.ax2 = None, None, None
        self.ani = None
        # self.grouped_logs = defaultdict(list)


    # Function to append a new master log
    def log_master_device(self, time, device_name,ip_address, color, ldrvalue):
        self.log_entry_no = self.log_entry_no + 1 
        log_entry = {
            "log_entry_no": self.log_entry_no,
            "timestamp": time,  
            "master_device": device_name,
            "ip_address": ip_address,
            "color": color,
            "ldr_value": ldrvalue
        }
        self.master_log.append(log_entry)

    def calculate_masters_cumulative_time(self, master_id, ip_address, log_entries):
                
                    # Update the master time data
                    Master_name = f"Device ID: {master_id} \nIP address: {ip_address}"
                    if Master_name not in self.master_cumulative_times:
                        self.master_cumulative_times[Master_name] = 0  # Initialize cumulative time
                    self.master_cumulative_times[Master_name] += 1  # Increment cumulative time (assumes 1-second intervals)

    def extract_master_data(self, current_master_data):
        """Extract and store data for the current master device."""
        if current_master_data:
            try:
                print("Current Master:", current_master_data)
                for master_id, master_info in current_master_data.items():
                    # Extract individual values from the master_info dictionary
                    self.current_time = master_info.get("time", None)
                    self.ip_address = master_info.get("ip_address", None)
                    self.port = master_info.get("port", None)
                    self.led_attached = master_info.get("led_attached", None)  # Color of the device
                    self.ldr_value = master_info.get("ldr_value", None)
                    self.is_master = master_info.get("is_master", False)

                    # If it's a new device, assign a random color
                    if master_id not in self.device_colors:
                        self.device_colors[master_id] =  self.led_attached

                self.log_master_device(self.current_time, master_id, self.ip_address, self.device_colors[master_id], self.ldr_value)
                self.calculate_masters_cumulative_time(master_id, self.ip_address, self.master_log)
                return True
            except Exception as e:
                print(f"Error extracting master data: {e}")
                return False
        else:
            print("No master device found.")
            return False

    def plot_line_graph(self):
        """Update the line graph with LDR values over time."""
        self.ax1.clear()

        # Extract the last 30 entries
        last_30_entries = self.master_log[-30:]
        last_entry = self.master_log[-1]

        # Access values for specific keys
        log_entry_no = last_entry['log_entry_no']
        timestamp = last_entry['timestamp']
        master_device = last_entry['master_device']
        ip_address = last_entry['ip_address']
        color = last_entry['color']
        ldr_value = last_entry['ldr_value']
        
        if log_entry_no is None:
            return

        # Combine data from all devices into a single list of points
        all_points = []
        
        for plot_point in last_30_entries:
            log_entry_no = plot_point["log_entry_no"]
            master_device = plot_point["master_device"]
            ldr_value = plot_point["ldr_value"]
            all_points.append((log_entry_no, ldr_value, master_device))

        # Sort points by log_entry_no to ensure they are in chronological order
        all_points.sort(key=lambda x: x[0])  # Sort by log_entry_no

        # Keep track of which devices have already been labeled
        labeled_devices = set()

        # Plot data and lines for all devices
        for i in range(len(all_points) - 1):
            current_point = all_points[i]
            next_point = all_points[i + 1]

            # Unpack points
            x1, y1, master_device1 = current_point
            x2, y2, master_device2 = next_point

            # Get color (can be different for each device, or use the same)
            color = self.device_colors.get(master_device1, "grey")

            # Plot the points (only label the first device of each set of points)
            label = master_device1 if master_device1 not in labeled_devices else None
            labeled_devices.add(master_device1)

            # Plot the points
            self.ax1.scatter(x1, y1, color=color, marker='o', label=label)
            self.ax1.scatter(x2, y2, color=color, marker='o')

            # Draw a line between the current point and the next point
            self.ax1.plot([x1, x2], [y1, y2], color=color, linestyle='-', linewidth=1)

        # Set plot labels and title
        self.ax1.set_xlabel('Time')
        self.ax1.set_ylabel('LDR Value')
        self.ax1.set_title('LDR Reading (Line Graph)')

        # Show legend, grid, etc.
        self.ax1.legend()
        self.ax1.grid()
    def plot_bar_chart(self):
            """Update the bar chart with cumulative time data."""
            self.ax2.clear()
            masters = list(self.master_cumulative_times.keys())
            times = list(self.master_cumulative_times.values())
            # Loop through each master and assign the same color from device_colors
            bar_colors = []
            # for master, time in zip(masters, times):
            #     bar_colors.append(self.device_colors.get(master, 'gray'))  # Default to gray if no color assigned
            for master in masters:
                master_id = master.split(' ')[2]  # Extract device ID from Master_name (e.g., Device ID: <ID>)
                bar_colors.append(self.device_colors.get(master_id, 'gray'))  # Default to gray if no color assigned
            self.ax2.bar(masters, times, color=bar_colors)  # Assign colors for the bars
            self.ax2.set_xlabel('Master ID')
            self.ax2.set_ylabel('Active Time (s)')
            self.ax2.set_title('Cumulative Active Time per Master')
            self.ax2.grid()

    def run_graph_update(self, frames):
        try:
            current_master_data = self.Master.get_current_master()  
            if self.extract_master_data(current_master_data):
                self.plot_line_graph()
                self.plot_bar_chart()
        except Exception as e:
            print(f"Error in run_graph_update: {e}")

    def start(self):
        plt.ion()  # Turn on interactive mode
        # Set up Matplotlib figure and axes
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 8))
        self.ani = FuncAnimation(self.fig, self.run_graph_update, interval=1000, cache_frame_data=False)
        plt.pause(0.1)

    def stop(self):
        plt.ioff()  # Turn off interactive mode
        # Close the plot after it’s done rendering
        plt.close()
        print("Graph updater stopped.")

class HandshakeManager:
    def __init__(self, socket_manager, device_token, online_interval=10):
        self.socket_manager = socket_manager
        self.device_token = device_token
        self.online_interval = online_interval  # Keep this as an integer
        self.online_timer = None  # Initialize timer as None

    def send_udp_message(self, message):
        """Send a UDP message using the socket manager."""
        try:
            return self.socket_manager.send_udp_message(message)
        except Exception as e:
            print(f"Error sending UDP message: {e}")
            return False

    def start_handshake(self):
        """Send the handshake message."""
        message = f"{self.device_token}@{self.device_token}@ONLINE@"
        if self.send_udp_message(message):
            # print("Sent start handshake.")
            return True
        else:
            print("Failed to send start handshake.")
            return False

    def stop_handshake(self):
        """Send the stop handshake message."""
        message = f"{self.device_token}@{self.device_token}@RESET@"
        for i in range(10):
            self.send_udp_message(message)
        if self.send_udp_message(message):
            print("Sent stop handshake.")
            return True
        else:
            print("Failed to send stop handshake.")
            return False

    def start_online_indicator(self):
        """Start a repeating online indicator using a timer."""
        def send_and_restart():
            # Send the handshake and restart the timer
            self.start_handshake()
            self.start_online_indicator()  # Restart timer

        # Cancel the existing timer if it exists
        if self.online_timer is not None:
            self.online_timer.cancel()

        # Create a new timer
        self.online_timer = Timer(self.online_interval, send_and_restart)
        self.online_timer.start()
        # print(f"Started online indicator with {self.online_interval}s interval.")

    def stop_online_indicator(self):
        """Stop the online indicator."""
        if self.online_timer is not None:
            self.online_timer.cancel()
            self.online_timer = None
            print("Stopped the online indicator.")
        else:
            print("No online indicator to stop.")
class LEDFlashingManager:
    def __init__(self, led_reset, led_red, led_green, led_blue, ldr_min, ldr_max, flashing_min, flashing_max):
        self.led_reset = led_reset
        self.led_red = led_red
        self.led_green = led_green
        self.led_blue = led_blue
        self.ldr_min = ldr_min
        self.ldr_max = ldr_max
        self.flashing_min = flashing_min
        self.flashing_max = flashing_max
        self.flashing_rate = 0
        self.flashing_color = None

    def reset_indication(self):
        self.led_reset.on()
        time.sleep(3)
        self.led_reset.off()

    def reset_leds(self):
        self.led_reset.off()
        self.led_red.off()
        self.led_green.off()
        self.led_blue.off()

    def map_value(self, x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_max

    def blink(self, led_key, ldr_data):
        if led_key and ldr_data:
            blink_rate = float(ldr_data)
            self.flashing_rate = self.map_value(blink_rate, self.ldr_min, self.ldr_max, self.flashing_min, self.flashing_max)
            self.stop_blinking()
            if led_key == "RED":
                self.flashing_color = "RED"
                self._blink_red()
            elif led_key == "BLUE":
                self.flashing_color = "BLUE"
                self._blink_blue()
            elif led_key == "GREEN":
                self.flashing_color = "GREEN"
                self._blink_green()

    def _blink_red(self):
        if self.flashing_color == "RED":
            self.led_red.toggle()
            Timer(self.flashing_rate, self._blink_red).start()

    def _blink_green(self):
        if self.flashing_color == "GREEN":
            self.led_green.toggle()
            Timer(self.flashing_rate, self._blink_green).start()

    def _blink_blue(self):
        if self.flashing_color == "BLUE":
            self.led_blue.toggle()
            Timer(self.flashing_rate, self._blink_blue).start()

    def stop_blinking(self):
        self.flashing_color = None
        Timer(self.flashing_rate, self._blink_red).cancel()
        Timer(self.flashing_rate, self._blink_green).cancel()
        Timer(self.flashing_rate, self._blink_blue).cancel()
        self.reset_leds()

  
class MasterManager:
    def __init__(self):
        # Dictionary to hold data for all devices
        self.master_data = {}

    def update_master_data(self, master_id, ldr_value, ip_address=None, port=None, led_attached=None):
        """Update or initialize master data. Ensure only one master device at a time."""
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
         # Reset the current master device to non-master
        current_master_data = self.get_current_master()
        
        if current_master_data != None:
            current_master_id, current_master_info = list(current_master_data.items())[0]
            self.master_data[current_master_id]["is_master"] = False
        # set the color of the graphs 
        if led_attached == "RED":
            led_color = "red"
        if led_attached == "BLUE":
            led_color = "blue"
        if led_attached == "GREEN":
            led_color = "green"
            
        if master_id not in self.master_data:
             # Initialize data for the master if not present
            print(f"Initialize data for the new Master :{master_id}") 
            self.master_data[master_id] = {
                    "time": current_time,
                    "ip_address": ip_address,
                    "port": port,
                    "led_attached": led_color,
                    "ldr_value": ldr_value,
                    "is_master": True,
                }
            print(f"Data for the new Master :{self.master_data[master_id]}") 
            print(f"Get every master data  :{self.get_master_data()}") 
        else:
            # Update existing master data
            self.master_data[master_id].update({
                    "time": current_time,
                    "ldr_value": ldr_value,
                    "is_master": True,
                    "ip_address": ip_address or self.master_data[master_id]["ip_address"],
                    "port": port or self.master_data[master_id]["port"],
                    "led_attached": led_color or self.master_data[master_id]["led_attached"],
                })

    def get_master_data(self):
        """Retrieve all master data."""
        return self.master_data.copy()

    def get_master_data_by_id(self, master_id):
        """Retrieve data for a specific master."""
        return self.master_data.get(master_id, {})

    def get_current_master(self):
     """Retrieve the current master device."""
     # Iterate through each device in master_data
     for master_id, master_info in self.master_data.items():
        # print(f"master_id: {master_id}, master_info: {master_info}")
        if master_info.get("is_master", False):  # Check if the 'is_master' key is True
            return {master_id: master_info}  # Return the master device's data as a dictionary
     return None  # If no master is found
        
class SystemController:
    LED_RESET_PIN = 23
    LED_RED_PIN = 24
    LED_GREEN_PIN = 20
    LED_BLUE_PIN = 25
    INPUT_BUTTON_PIN = 16
    
    LDR_RAW_MIN = 0
    LDR_RAW_MAX = 1023
    FLASHING_FREQUENCY_MIN = 0.1
    FLASHING_FREQUENCY_MAX = 1
    ONLINE_INDICATION_TIMER = 10

    RASP_Device_Token_ID = "RaspBerry_PI_5"
    LED_MAPPING_DICT = {"RED": None, "BLUE": None, "GREEN": None}

    def __init__(self, broadcast_ip='255.255.255.255', broadcast_port=54321, log_dir="logs"):
        self.resetled = LED(self.LED_RESET_PIN)
        self.rled = LED(self.LED_RED_PIN)
        self.gled = LED(self.LED_GREEN_PIN)
        self.bled = LED(self.LED_BLUE_PIN)
        self.button = Button(self.INPUT_BUTTON_PIN)
        self.flashingRateValue = 0
        self.flashingcolor = None

        self.process_stage = STATUS.IDLE
        self.button.when_pressed = self.on_button_press

        # Instantiate other managers
        self.wifi_manager = WiFiManager()
        self.socket_manager = SocketManager(broadcast_ip, broadcast_port)  # Pass the parameters
        self.handshake_manager = HandshakeManager(self.socket_manager, self.RASP_Device_Token_ID,self.ONLINE_INDICATION_TIMER)
        self.Mastermanager = MasterManager()
        self.graph_updater = GraphUpdater(self.Mastermanager)
        self.logger = Logger(log_dir, self.graph_updater)  # Pass the graph_updater  and directory

        self.led_flashing_manager = LEDFlashingManager(self.resetled, self.rled, self.gled, self.bled, self.LDR_RAW_MIN, self.LDR_RAW_MAX, self.FLASHING_FREQUENCY_MIN, self.FLASHING_FREQUENCY_MAX)
        self.led_flashing_manager.reset_leds()
        self.reset_mapping()


    def reset_mapping(self):
        for key in self.LED_MAPPING_DICT:
            self.LED_MAPPING_DICT[key] = None

        self.Mastermanager.master_data = {} 
       # 
        self.graph_updater.ldr_data = {} 
        self.graph_updater.master_cumulative_times = {} 
        self.graph_updater.device_colors = {} 
        self.graph_updater.master_log = [] 
      #

    def on_button_press(self):
            print("Button pressed.")
            if self.process_stage == STATUS.IDLE:  
                self.process_stage = STATUS.STOP  
            elif self.process_stage == STATUS.START_VISUALIZATION or self.process_stage == STATUS.START_COLLECTING:
                self.process_stage = STATUS.STOP  

    def cleanup(self):
            print("cleanup resetting everything.")
            self.led_flashing_manager.stop_blinking()
            self.logger.close_log()
            self.graph_updater.stop()
            self.led_flashing_manager.reset_indication()
            self.reset_mapping()
            self.process_stage = STATUS.START_VISUALIZATION
        
    def configure_master(self, master_id):
        # Check if the MASTER is already mapped
        for key in self.LED_MAPPING_DICT:
            if self.LED_MAPPING_DICT[key] == master_id:
                # print(f"The MASTER ESP8266: {master_id} is already configured with {key}")
                return key

        # Configure the new MASTER if it's not mapped
        print(f"Configuring the New MASTER ESP8266: {master_id}")
        for key in self.LED_MAPPING_DICT:
            if self.LED_MAPPING_DICT[key] is None:
                self.LED_MAPPING_DICT[key] = master_id
                print(f"New MASTER ESP8266: {master_id} configured with {key}")
                return key

        # Return None if no mapping was possible
        print(f"Failed to configure MASTER ESP8266: {master_id}. No available LEDs.")
        return None
    def handle_sensor_data(self, sensordata, ipdata):
        separator = "@"
        data = sensordata.split(separator)
        if data[0] == "ESP_8266":
            if data[1] == "MASTER":
                master = data[2]
                ip = ipdata[0]
                port = ipdata[1]
                photocell_value = int(data[4])  # data[4] holds photocell data
                LED_key = self.configure_master(master)
                if(LED_key != None): 
                    self.Mastermanager.update_master_data(master, photocell_value, ip, port, LED_key)
                    self.led_flashing_manager.blink(LED_key,photocell_value)
    def run(self):
    
        time.sleep(1)
        while True:
            if self.process_stage == STATUS.IDLE:
                while self.process_stage == STATUS.IDLE:
                    if self.wifi_manager.check_wifi():
                        print("Raspberry is online")
                    else:
                        self.wifi_manager.reconnect_wifi()
                    time.sleep(1)
                    if self.socket_manager.initialize_socket():
                        if self.handshake_manager.start_handshake():
                          self.handshake_manager.start_online_indicator()
                        print("Raspberry is online, initialize_socket waiting for the button press")
                        # self.process_stage = STATUS.STOP


            elif self.process_stage == STATUS.START_VISUALIZATION:
                        self.graph_updater.start()
                        self.logger.create_new_log()
                        self.process_stage = STATUS.START_COLLECTING
                    
            elif self.process_stage == STATUS.START_COLLECTING:
                while self.process_stage == STATUS.START_COLLECTING:
                    data, ip_data = self.socket_manager.receive_sensor_data()
                    if data != None:
                        self.handle_sensor_data(data, ip_data)
                    plt.pause(0.1)
            elif self.process_stage == STATUS.STOP:
                self.handshake_manager.stop_online_indicator()
                if self.handshake_manager.stop_handshake():
                   self.cleanup()


if __name__ == "__main__":
        # Customize broadcast IP and port as needed
        system_controller = SystemController(broadcast_ip='255.255.255.255', broadcast_port=54321, log_dir="my_logs")
        system_controller.run()





# #  -----------------   end of the Assignment ------------------
