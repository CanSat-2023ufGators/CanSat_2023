import time
import serial.tools.list_ports

# Serial port set up
ports = serial.tools.list_ports.comports()
serialInst = serial.Serial()
portsList = []
portVar = "COM4"

# Select which port to connect to
for onePort in ports:
    print(onePort)

portVar = input("Enter the port (e.g. \"COM11\"): ")
# Initialize serial object thing
serialInst.baudrate = 9600
serialInst.port = portVar
serialInst.open()

command = "CMD,1071,CX,ON"
serialInst.write(command.encode('utf-8'))
time.sleep(2)

# Transmitting data to Arduino via serial port
# while True:
#     # command = input("Arduino Command: ")
#     # serialInst.write(command.encode('utf-8'))
#     command = "CMD,1071,CX,ON"
#     serialInst.write(command.encode('utf-8'))
#     time.sleep(1)
#     if command == 'CMD,1071,CX,OFF':
#         exit()

# Check port for received data

while True:
    data = serialInst.readline().strip()
    if data:
        print(data)