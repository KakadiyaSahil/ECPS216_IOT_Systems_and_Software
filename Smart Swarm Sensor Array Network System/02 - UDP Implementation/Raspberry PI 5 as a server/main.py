import os
import subprocess
import socket
import time


# Light intensity thresholds
LOW_INTENSITY_LEVEL_MIN = 0
LOW_INTENSITY_LEVEL_MAX = 300
MEDIUM_INTENSITY_LEVEL_MIN = 301
MEDIUM_INTENSITY_LEVEL_MAX = 600
HIGH_INTENSITY_LEVEL_MIN = 601
HIGH_INTENSITY_LEVEL_MAX = 1023

# Target ESP8266 device IP address and port number for UDP communication
ESP_target_ip = '192.168.137.6'  # Replace with actual ESP IP address
ESP_target_port = 54321  # Port number used by the ESP8266

# Raspberry Pi identifier
RASP_Device_Token_ID = "RaspBerry_PI_5"

# Variables to track program state and lost packets
Program_Start = False
Lost_report_num = 0

# Initialize a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Function to check Wi-Fi connectivity
def check_wifi():
    try:
        # Try to connect to Google's DNS server (8.8.8.8) to check connectivity
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        print("Connected to Wi-Fi.")
        return True
    except OSError:
        print("Not connected to Wi-Fi.")
        return False

# Function to reconnect to Wi-Fi
def reconnect_wifi():
    print("Attempting to reconnect to Wi-Fi...")
    os.system("sudo wpa_cli -i wlan0 reconfigure")  # Reconfigures wlan0
    time.sleep(10)  # Wait for Wi-Fi to reconnect

# Function to initialize a socket
# Returns True and the socket object if successful, False otherwise
def socket_inilization(receiving_port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("Socket initialized successfully")
        sock.settimeout(2)  # Set a timeout for the socket
        return True, sock
    except Exception as e:
        print(f"Error: {e}")
        return False

# Function to deactivate the socket (close it)
# Returns True if successful, False otherwise
def socket_deactivate(receiving_port):
    try:
        sock.close()  # Close the socket
        print("Socket closed and port unbound.")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

# Function to receive sensor data from the ESP8266
# Returns True if data is received from the target IP, otherwise False
def getSensorData(sock):
    try:
        # Wait for sensor data from the targeted device
        sensordata, addr = sock.recvfrom(1024)  # Buffer size of 1024 bytes
        print(f"Received SensorData from the targeted device {addr}: Data: {sensordata.decode()}")
        return True, False, sensordata.decode()
    except Exception as e:
        print(f"Error: {e}")
        return False, False, e

# Function to send a UDP message to the target IP and port
# Returns True if successful, False otherwise
def send_UDP_message(sock, message, target_ip, target_port):
    try:
        print(f"Sending UDP message: {message} to IP: {target_ip}, Port: {target_port}")
        sock.sendto(message.encode(), (target_ip, target_port))  # Send the message
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

# Function to check if the target IP is reachable via ping
# Returns True if reachable, False otherwise
def is_ip_reachable(target_ip):
    print(f"Scanning for IP address {target_ip} ...")
    try:
        result = subprocess.run(["ping", "-c", "1", target_ip], stdout=subprocess.PIPE)  # Ping once
        if result.returncode == 0:
            print(f"IP {target_ip} is reachable.")
            return True
        else:
            print(f"IP {target_ip} is not reachable.")
            return False
    except Exception as e:
        print(f"Error scanning for IP: {e}")
        return False

# Function to start the handshake process with the ESP8266
# Returns True if successful
def start_handshake_establishment(sock, target_ip, target_port):
    print(f"Establishing the Handshake with IP: {target_ip}, Port: {target_port}")
    status = False
    message = RASP_Device_Token_ID +"@"+ "START_SYNC" +  "@" # Message to initiate synchronization
    if send_UDP_message(sock, message, target_ip, target_port):
        status = True
    return status

# Function to stop the handshake process
# Returns True if successful
def stop_handshake_establishment(target_ip, target_port):
    print(f"Stopping the Handshake with IP: {target_ip}, Port: {target_port}")
    status = False
    message = RASP_Device_Token_ID +"@"+ "STOP_SYNC" +  "@" # Message to stop synchronization
    if send_UDP_message(sock, message, target_ip, target_port):
        status = True
    return status


# Main function to automate the process
def main():

    while True:

        # Step 1: Check Wi-Fi connection
        while not check_wifi():
            # Step 2: If not connected, attempt to reconnect
            reconnect_wifi()


        # Step 3: Check if the ESP device is reachable
        while not is_ip_reachable(ESP_target_ip):
            time.sleep(10)

         # Step 4: Establish handshake with the ESP device
        while not start_handshake_establishment(sock, ESP_target_ip, ESP_target_port):
            time.sleep(10)
        while True :
            # Sensor data loop
                sensordata = 0.0
                data_status, time_out, data = getSensorData(sock)
                if data_status:
                        print(f"Data value: {data}")
                        # Convert received sensor data to an integer
                        sensordata = float(data)
                        # Handle LED states based on the intensity levels of the sensor data
                        if (LOW_INTENSITY_LEVEL_MIN <= sensordata <= LOW_INTENSITY_LEVEL_MAX):
                            print("Red LED for low intensity") 
                        elif (MEDIUM_INTENSITY_LEVEL_MIN <= sensordata <= MEDIUM_INTENSITY_LEVEL_MAX):
                            print("Red LED for low intensity")     
                        elif (HIGH_INTENSITY_LEVEL_MIN <= sensordata <= HIGH_INTENSITY_LEVEL_MAX):
                            print("Red LED for low intensity") 
                elif time_out:
                        # If no data is received, track the number of lost packets
                        Lost_report_num += 1
                        if Lost_report_num >= 5:
                            break


# Run the main function when the script is executed
if __name__ == "__main__":
    main()