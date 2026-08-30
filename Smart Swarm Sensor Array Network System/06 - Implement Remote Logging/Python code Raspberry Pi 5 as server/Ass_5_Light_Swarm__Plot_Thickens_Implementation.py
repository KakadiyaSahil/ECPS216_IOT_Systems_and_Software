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
from gpiozero import LED, Button, OutputDevice
import time
from threading import Timer
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from queue import Queue
from datetime import datetime
import re
import threading
import requests

# ==========================
# GPIO Pin Definitions
# ==========================
from gpiozero import OutputDevice
import time
import threading

class SevenSegmentDisplay:
    def __init__(self, led_pins, col_pins, digit_patterns):
        """
        Initialize the 7-segment display.
        
        Args:
            led_pins: List of GPIO pins for 7-segment segments (A-G + DP).
            col_pins: List of GPIO pins for digit columns.
            digit_patterns: List of segment patterns for digits 0-9.
        """
        self.led_devices = [OutputDevice(pin) for pin in led_pins]
        self.col_devices = [OutputDevice(pin) for pin in col_pins]
        self.digit_patterns = digit_patterns
        self.digits = [0, 0, 0, 0]  # Default digits to display
        self.running = False
        self.threads = []

    def set_digits(self, digits):
        """
        Set the digits to be displayed.
        
        Args:
            digits: List of 4 digits to display (values between 0-9).
        """
        self.digits = digits

    def extract_last_three_digits(self, ip_address):
        # Split the IP address into parts
        octets = ip_address.split('.')
        
        # Extract the last octet (last portion of the IP)
        last_octet = octets[-1]
        
        # Pad the last octet to ensure it has three characters
        padded_octet = last_octet.zfill(3)
        
        # Split the padded octet into individual digits and convert to integers
        last_three_digits = [int(digit) for digit in padded_octet]
    
        return last_three_digits

    def _display_digit(self, digit, col_idx):
        """
        Multiplexing logic for a single digit (runs in a thread).
        
        Args:
            digit: The digit to display (0-9).
            col_idx: Index of the column to activate.
        """
        while self.running:
            # print(f"last_three_digits: {self.digits}")
            # Turn off all columns
            for col in self.col_devices:
                col.value = 0

            # Activate the specific column
            self.col_devices[col_idx].value = 1

            # Set the segment LEDs
            for seg_idx in range(7):  # A-G segments
                self.led_devices[seg_idx].value = self.digit_patterns[self.digits[col_idx]][seg_idx]

            # Handle the decimal point (DP at index 7)
            self.led_devices[7].value = 0  # Adjust logic for DP as needed
            # plt.pause(0.001)
            # Brief delay for stabilization
            time.sleep(0.0005)

            # Turn off the column
            # self.col_devices[col_idx].value = 0

    def start(self):
        """
        Start the display by launching threads for each digit.
        """
        self.running = True
        for col_idx in range(3):  # Create a thread for each column
            thread = threading.Thread(target=self._display_digit, args=(self.digits[col_idx], col_idx))
            self.threads.append(thread)
            thread.start()

    def stop(self):
        """
        Stop the display and clean up resources.
        """
        self.running = False
        for thread in self.threads:
            thread.join()  # Wait for all threads to finish

        # Turn off all LEDs and columns
        for led in self.led_devices:
            led.off()
        for col in self.col_devices:
            col.off()

        print("Display stopped and cleaned up.")

# Configuration for GPIO pins and digit patterns
LEDs = [24, 4, 17, 19, 13, 6, 27, 5]  # GPIO pins for 7-segment A-G + DP
cols = [22, 0, 2]  # GPIO pins for columns
nums = [
    [0, 0, 0, 0, 0, 0, 1],  # 0 inverted
    [1, 0, 0, 1, 1, 1, 1],  # 1 inverted
    [0, 0, 1, 0, 0, 1, 0],  # 2 inverted
    [0, 0, 0, 0, 1, 1, 0],  # 3 inverted
    [1, 0, 0, 1, 1, 0, 0],  # 4 inverted
    [0, 1, 0, 0, 1, 0, 0],  # 5 inverted
    [0, 1, 0, 0, 0, 0, 0],  # 6 inverted
    [0, 0, 0, 1, 1, 1, 1],  # 7 inverted
    [0, 0, 0, 0, 0, 0, 0],  # 8 inverted
    [0, 0, 0, 1, 1, 0, 0],  # 9 inverted
]

# Initialize the display
# display = SevenSegmentDisplay(LEDs, cols, nums)
# ------------------------------ SPI Led Strips ---------------------------------
import spidev
import time

class LEDMatrix:
    def __init__(self, spi_bus=0, spi_device=0):
        """Initialize the SPI communication and MAX7219 settings."""
        # SPI Configuration
        self.spi_bus = spi_bus       # SPI bus (0 or 1)
        self.spi_device = spi_device # SPI device (CE0 = 0, CE1 = 1)
        self.spi = spidev.SpiDev()
        self.spi.open(self.spi_bus, self.spi_device)

        # Set SPI speed and mode
        self.spi.max_speed_hz = 8000000  # 8 MHz
        self.spi.mode = 0  # SPI mode 0 (CPOL=0, CPHA=0)

        # MAX7219 Registers
        self.MAX7219_REG_NOOP = 0x00  # No Operation
        self.MAX7219_REG_DIGIT0 = 0x01
        self.MAX7219_REG_DIGIT1 = 0x02
        self.MAX7219_REG_DIGIT2 = 0x03
        self.MAX7219_REG_DIGIT3 = 0x04
        self.MAX7219_REG_DIGIT4 = 0x05
        self.MAX7219_REG_DIGIT5 = 0x06
        self.MAX7219_REG_DIGIT6 = 0x07
        self.MAX7219_REG_DIGIT7 = 0x08
        self.MAX7219_REG_DECODEMODE = 0x09
        self.MAX7219_REG_INTENSITY = 0x0A
        self.MAX7219_REG_SCANLIMIT = 0x0B
        self.MAX7219_REG_SHUTDOWN = 0x0C
        self.MAX7219_REG_DISPLAYTEST = 0x0F

        # Initialize the MAX7219
        self.init_max7219()

    def init_max7219(self):
        """Initialize the MAX7219 and configure settings."""
        self.spi.xfer2([self.MAX7219_REG_SHUTDOWN, 0x01])  # Turn on the display
        self.spi.xfer2([self.MAX7219_REG_SCANLIMIT, 0x07])  # Set scan limit to 8 rows
        self.spi.xfer2([self.MAX7219_REG_DECODEMODE, 0x00])  # Disable decode mode (manual control)
        self.spi.xfer2([self.MAX7219_REG_INTENSITY, 0x0F])  # Set maximum brightness
        self.spi.xfer2([self.MAX7219_REG_DISPLAYTEST, 0x00])  # Disable display test mode

    def set_row(self, row, value):
        """Set the LEDs of a specific row (0-7)."""
        if row < 0 or row > 8:
            raise ValueError("Row must be between 0 and 7")
        self.spi.xfer2([self.MAX7219_REG_DIGIT0 + row, value])

    def set_led(self, x, y, value):
        """Turn on or off a specific LED at position (x, y)."""
        if value == 1:
            row_data = 1 << x  # Set the x-th bit to 1
        else:
            row_data = 0  # Turn off the LED
        self.set_row(y, row_data)

    def clear_matrix(self):
        """Clear the entire LED matrix."""
        for row in range(8):
            self.set_row(row, 0)  # Set each row to 0 (turn off all LEDs)

    def get_ldr_value_averages(self, log):
        """Calculate the average ldr_value for every 4th element in the last 32 entries."""
        # Get the last 32 entries
        last_32_entries = log[-32:]
        if len(last_32_entries) // 4 :
            # Extract the ldr_value from each entry
            ldr_values = [entry["ldr_value"] for entry in last_32_entries]

            # Calculate the average of every 4 ldr_values
            averages = []
            for i in range(0, len(ldr_values), 4):  # Iterate in steps of 4
                avg = sum(ldr_values[i:i+4]) / 4  # Sum of the 4 elements and divide by 4
                averages.append(avg)
            return averages
        else:
            return None
        
    
    def matrix_leds(self, data, selected_col, color, max_row = 8, max_data = 1024):
        fraction_VALUE = max_data // (max_row + 1)
            # Initialize the row data to 0 (all LEDs off initially)
        row_data = 0

        # Loop over each row and set the appropriate LEDs
        for row in range(max_row):
            if data > (row * fraction_VALUE):  # 1024/8 = 128, scale the value
                row_data |= (1 << row)  # Turn on the LED at the current row
            else:
                row_data &= ~(1 << row)  # Turn off the LED at the current row

        # Pass the entire row_data to set_row to update the LEDs in the selected column
        self.set_row(selected_col, row_data)

    def close(self):
        """Clear the matrix and close the SPI connection."""
        self.clear_matrix()  # Clear the display when the program is interrupted


# ------------------------------ SPI Led Strips ---------------------------------

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
        self.listensock = None
        self.LISTEN_PORT = 12346
        self.broadcast_ip = broadcast_ip
        self.broadcast_port = broadcast_port
       # Get the host name of the machine
        # hostname = socket.gethostname()
        # self.ip_address = socket.gethostbyname(hostname)
        self.ip_address = "192.168.137.230"
    


    def initialize_socket(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.sock.bind((self.broadcast_ip, self.broadcast_port))
            self.listensock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.listensock.bind((self.ip_address, self.LISTEN_PORT))  # Listen on all interfaces for the given port
            self.listensock.settimeout(5)
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
            # print(f"Sent UDP message: {message}")
            return True
        except Exception as e:
            print(f"Error sending UDP message: {e}")
            return False

    def receive_sensor_data(self):
        try:
            sensordata, addr = self.listensock.recvfrom(1024)
            return sensordata.decode(), addr
        except socket.timeout:
            print("Sensor data receive timed out.")
            return None, None

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
        self.led_matrix = LEDMatrix()
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
        # print(f"Current log entry: {log_entry}")
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
                # print("Current Master:", current_master_data)
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

# ------------------------------ SPI Led Strips ---------------------------------
        average_list = self.led_matrix.get_ldr_value_averages(self.master_log[-32:])   
        print(f"Averages list of every 4 ldr_value: {average_list}")
        if average_list is not None:
            for i in range(0, 8):
                if i < len(average_list):  # If average is non-zero, display it
                    avg = average_list[i]
                    # print(f"Group {i}: {avg}")
                    self.led_matrix.matrix_leds(avg, i, "red")
                else:  # If average is zero or not valid, set to default (0)
                    # print(f"Group {i}: 0 (No data)")
                    self.led_matrix.matrix_leds(0, i, "red")  # Display 0 or default value
        else:
            # print("No data available to display on LED matrix.")
            for i in range(0, 8):  # Assuming 8 rows (adjust for your needs)
                # print(f"Group {i}: 0 (No data)")
                self.led_matrix.matrix_leds(0, i, "red")
# ------------------------------ SPI Led Strips ---------------------------------

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
                last_entry = self.master_log[-1]
                url = "http://192.168.137.230:1880/Last_Log_Entry"
                response = requests.post(url, json=last_entry)

                masters = list(self.master_cumulative_times.keys())
                times = list(self.master_cumulative_times.values())


                # Regex pattern to extract Device ID and IP Address
                pattern = r'Device ID:\s+(\S+)\s*?\nIP address:\s+([\d\.]+)'

                # Process each string in the list and store results in a dictionary list
                device_info_list = []
                for entry in masters:
                    matches = re.findall(pattern, entry)  # Extract matches from each string
                    for device_id, ip_address in matches:
                        # Create a dictionary for each match
                        master_data = self.Master.get_master_data_by_id(device_id)
                        led_attached_value = master_data.get('led_attached', 'default_value') 
                        up_time_value = self.master_cumulative_times.get(entry, 0)  # Default value is 0 if key isn't found
                        device_info = {
                            "Device ID": device_id,
                            "IP Address": ip_address,
                            "Up Time": up_time_value,
                            "color": led_attached_value
                        }
                        # Append the dictionary to the list
                        device_info_list.append(device_info)
                # Print the final list of dictionaries
                # print(device_info_list)
                url = "http://192.168.137.230:1880/master_cumulative_times"
                response = requests.post(url, json=device_info_list)

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
        self.led_matrix.close()
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
        
        message = f"{self.device_token}@{self.device_token}@ONLINE@{self.socket_manager.LISTEN_PORT}@"
        if self.send_udp_message(message):
            # print(f"Sent start handshake. {message}")
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
        # print(f"led_attached :{led_attached}") 
        # print(f"port :{port}") 
        # print(f"ip_address :{ip_address}") 
        

        # set the color of the graphs 
        if led_attached == "RED":
            led_color = "red"
        if led_attached == "BLUE":
            led_color = "blue"
        if led_attached == "GREEN":
            led_color = "green"
        if led_attached == "YELLOW":
            led_color = "yellow"
        if led_attached == "ORANGE":
            led_color = "orange"
        if led_attached == "BLACK":
            led_color = "black"

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
            print(f"Data for the current Master :{self.master_data[master_id]}") 


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
    LED_RESET_PIN = 21
    LED_RED_PIN = 12
    LED_GREEN_PIN = 20
    LED_BLUE_PIN = 25
    INPUT_BUTTON_PIN = 16
    
    LDR_RAW_MIN = 0
    LDR_RAW_MAX = 1023
    FLASHING_FREQUENCY_MIN = 0.1
    FLASHING_FREQUENCY_MAX = 1
    ONLINE_INDICATION_TIMER = 2

    RASP_Device_Token_ID = "RaspBerry_PI_5"
    LED_MAPPING_DICT = {"RED": None, "BLUE": None, "GREEN": None, "YELLOW": None, "ORANGE": None, "BLACK": None}

 
    # Keep running for a while (simulate behavior)
    time.sleep(10)  # Display numbers for 10 seconds

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
        self.display = SevenSegmentDisplay(LEDs, cols, nums)   
        self.display.start()  
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
           
            url = "http://192.168.137.230:1880/Reset"
            response = requests.post(url, json={"device_cmd": "RESET"})
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
        # print(f"handle_sensor_data sensordata : {sensordata}")
        data = sensordata.split(separator)
        if data[0] == "ESP_8266":
            if data[1] == "MASTER":
                master = data[2]
                ip = ipdata[0]
                last_three_digits = self.display.extract_last_three_digits(ip)
                print(f"last_three_digits: {last_three_digits}")    
                self.display.set_digits(last_three_digits)
                port = ipdata[1]
                # print(f"handle_sensor_data data[4] : {data[4]}")
                photocell_value = int(data[4])  # data[4] holds photocell data
                # print(f"handle_sensor_data photocell_value : {photocell_value}")

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

                        
            elif self.process_stage == STATUS.START_VISUALIZATION:
                        self.graph_updater.start()
                        self.logger.create_new_log()
                        if self.handshake_manager.start_handshake():
                            self.handshake_manager.start_online_indicator()
                        self.process_stage = STATUS.START_COLLECTING
                    
            elif self.process_stage == STATUS.START_COLLECTING:
                while self.process_stage == STATUS.START_COLLECTING:
                    data, ip_data = self.socket_manager.receive_sensor_data()
                    if data != None:
                        self.handle_sensor_data(data, ip_data)
                    else:
                        time.sleep(5)
                    plt.pause(0.001)
            elif self.process_stage == STATUS.STOP:
                self.handshake_manager.stop_online_indicator()
                if self.handshake_manager.stop_handshake():
                   self.cleanup()




if __name__ == "__main__":
        # # Customize broadcast IP and port as needed
        system_controller = SystemController(broadcast_ip='255.255.255.255', broadcast_port=54321, log_dir="my_logs")
        system_controller.run()
        # app.run(host='0.0.0.0', port=5000)





# #  -----------------   end of the Assignment ------------------
