import csv
import queue
import re
import sys
import threading
import time
from datetime import datetime

import PySimpleGUI as sg
import matplotlib.pyplot as plt
import numpy as np
import serial.tools.list_ports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FormatStrFormatter

shared_data = queue.Queue()


def saveCSVfile(data):  # Saves telemetry data to CSV file
    header = ['TEAM_ID', 'MISSION_TIME', 'PACKET_COUNT', 'MODE', 'STATE', 'ALTITUDE', 'HS_DEPLOYED', 'PC_DEPLOYED',
              'MAST_RAISED', 'TEMPERATURE', 'VOLTAGE', 'PRESSURE', 'GPS_TIME', 'GPS_ALTITUDE', 'GPS_LATITUDE',
              'GPS_LONGITUDE', 'GPS_SATS', 'TILT_X', 'TILT_Y', 'CMD_ECHO']
    with open('Team_' + TEAM_ID + '.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data)


def readSimulationData():  # Reads simulation pressure data
    simulatedPressureData = []
    f = open("cansat_2023_simp.txt", "r")
    simulatedPressureData = []
    for line in f:
        if "CMD,$,SIMP," in line:
            simulatedPressureData.append(line[:-1].replace("$", "1071"))
    return simulatedPressureData


def readBackupData():  # Reads backup data
    backupData = []
    with open('backup_data.csv') as f:
        reader = csv.reader(f)
        for item in reader:
            tempData = []
            for data in item[:-1]:
                tempData.append(data)
            backupData.append(tempData)
    return backupData


def getTime():  # Get the current time
    return datetime.utcnow().time().strftime("%H:%M:%S")


def draw_figure(canvas, figure):  # Draws a figure to be saved to the window's layout
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


# Global variables
telemetryData = []  # Stores all telemetry data (list of lists)
simulationData = []  # Stores all simulation data (list of lists)
backupData = readBackupData()  # Stores the backup data (read from a file)
simulatedPressureData = readSimulationData()  # Stores the simulated pressure data (read from a file)
TEAM_ID = '1071'
MISSION_TIME = ""
PACKET_COUNT = 0
MODE = 'F'
STATE = 'LAUNCH_WAIT'
ALTITUDE = 0
HS_DEPLOYED = 'N'
PC_DEPLOYED = 'N'
MAST_RAISED = 'N'
TEMPERATURE = 0
VOLTAGE = 0
GPS_TIME = 0
GPS_ALTITUDE = 0
GPS_LATITUDE = 0
GPS_SATS = 0
TILT_X = 0
TILT_Y = 0
CMD_ECHO = ''
isCanSatON = False
simulationMode = False  # Toggle T/F if user activates SIM mode in GUI
simulationActivation = False  # Toggle T/F if user enables/disables SIM mode in GUI
recalibrate = False  # After you turn off simulation, recalibrate graphs
start = 0  # Start time value (gets initialized in the while loop when sim mode is enabled)
seconds = 1  # How many seconds have passed (for sim mode)
backupMode = False  # Backup data mode
dataReceived = False  # Was data received in the gui
connected = False  # Check if we are connected
calibrated = False  # check if are calibrated
xbee_sent = False
simulation_data_count = 0
backup_data_count = 1


def sendXBeeCommand(command):  # Send command
    try:
        temp = ""
        if command == "CMD,1071,CX,ON":
            temp = "1071,0,1,"
        elif command == "CMD,1071,CX,OFF":
            temp = "1071,0,0,"
        elif command == "CMD,1071,ST,GPS":
            temp = "1071,1,-1,"
        elif command == "CMD,1071,SIM,DISABLE":
            temp = "1071,2,0,"
        elif command == "CMD,1071,SIM,ACTIVATE":
            temp = "1071,2,1,"
        elif command == "CMD,1071,SIM,ENABLE":
            temp = "1071,2,2,"
        elif command == "CAL":
            temp = "1071,4,"
        elif command == "CMD,1071,CAL":
            temp = "1071,4,"
        elif command.find("SIMP") != -1:
            temp = f"1071,3,{command.split(',')[-1]},"
        elif command.find("ST") != -1:
            temp = f"1071,1,{command.split(',')[-1]},"
        elif command.find("OPEN") != -1:
            temp = f"1071,6,"
        elif command.find("CLOSE") != -1:
            temp = f"1071,7,"
        ser.write(temp.encode('utf-8'))
    except:
        print("Error transmitting command.")


def addXBeeInput(input, data):  # Takes input (string) and appends it to data (list of lists)
    input = input.split(',')
    tempLine = []
    for item in input:
        tempLine.append(item)
    data.append(tempLine)
    return data


def readXBeeData():  # Read data from serial port
    try:
        if not shared_data.empty():
            data = shared_data.get()
            if data:
                processedData = data[data.find('1071'):(data.rfind('1071') - 1)] + ","

                # Get the command
                command = data[data.rfind('1071'):]
                if command[-1] == "'": command = command[:-1]
                # CONVERT COMMAND TO STRING
                if command == "1071,0,1,":
                    command = "CX_ON"
                elif command == "1071,0,0,":
                    command = "CX_OFF"
                elif command == "1071,1,-1,":
                    command = "ST_GPS"
                elif command == "1071,2,0,":
                    command = "SIM_DISABLE"
                elif command == "1071,2,1,":
                    command = "SIM_ACTIVATE"
                elif command == "1071,2,2,":
                    command = "SIM_ENABLE"
                elif command == "1071,4,":
                    command = "CAL"
                elif command == "1071,6,":
                    command = "SERVO_OPEN"
                elif command == "1071,7,":
                    command = "SERVO_CLOSE"
                elif command.find("SIMP") != -1:
                    command = "SIMP_"
                elif command.find("ST") != -1:
                    command = "ST_"
                else:
                    command = ""
                # Add telemetry data to the list
                processedData = processedData.split(',')
                processedData.append(command)
                telemetryData.append(processedData)
                return True
    except:
        return False
    return False


# Create and switch to custom look and feel
sg.LOOK_AND_FEEL_TABLE['UFTheme'] = {'BACKGROUND': '#383535',
                                     'TEXT': '#F9F9FB',
                                     'INPUT': '#F9F9FB',
                                     'TEXT_INPUT': '#000000',
                                     'SCROLL': '#99CC99',
                                     'BUTTON': ('#F9F9FB', '#ffb84d'),
                                     'PROGRESS': ('#D1826B', '#CC8019'),
                                     'BORDER': 1, 'SLIDER_DEPTH': 0,
                                     'PROGRESS_DEPTH': 0, }
sg.theme('UFTheme')
_VARS = {'window': False,
         'gps_agg': False,
         'gpsPltFig': False,
         'altitude_agg': False,
         'altitudePltFig': False,
         'temp_agg': False,
         'tempPltFig': False,
         'voltage_agg': False,
         'voltagePltFig': False,
         'gyro_agg': False,
         'gyroPltFig': False
         }
plt.style.use('Solarize_Light2')  # Theme for pyplot

# Figure tab layouts
b_color = '#FDF6E3'
gps_layout = [[sg.Canvas(key='gpsCanvas', background_color=b_color, size=(100, 100))]]
altitude_layout = [[sg.Canvas(key='altitudeCanvas', background_color=b_color)]]
temp_layout = [[sg.Canvas(key='tempCanvas', background_color=b_color)]]
voltage_layout = [[sg.Canvas(key='voltageCanvas', background_color=b_color)]]
gyro_layout = [[sg.Canvas(key='gyroCanvas', background_color=b_color)]]

# Row layouts
first_row_A = [sg.Button('Connect'), sg.Button('Calibrate'), sg.Button('Power ON', button_color='#00b300'),
               sg.Button('Close', button_color='#DA3A3A')]
first_row_B = [
    [sg.Text('Team ID: ' + TEAM_ID, key='id'), sg.Text('Packet Count: ' + str(PACKET_COUNT), key='packet_count'),
     sg.Text('Mission Time: ' + getTime(), key='time'), ]]
second_row = [sg.Text('Mode: ' + str(MODE), key='mode'), sg.Text('State: ' + str(STATE), key='state'),
              sg.Text('GPS SATS: ' + str(GPS_SATS), key='sats'),
              sg.Text('GPS Mission Time: ', key='gps_mission_time'), ]
second_row_B = [sg.Text('Heat Shield Deployed: ' + HS_DEPLOYED, key='heat-shield'),
                sg.Text('Parachute Deployed: ' + PC_DEPLOYED, key='parachute'),
                sg.Text('Mast Raised: ' + MAST_RAISED, key='mast')]
misc_info = [
    [sg.Text("", key='msg')],
]
font_size_curr = 14
current_stat_cols = [
    [sg.Text("Altitude: ", key='cur_altitude', font=('Rockwell', font_size_curr))],
    [sg.Text("GPS Altitude: ", key='cur_gps_altitude', font=('Rockwell', font_size_curr))],
    [sg.Text("Pressure: ", key='cur_pressure', font=('Rockwell', font_size_curr))],
    [sg.Text("Temperature: ", key='cur_temp', font=('Rockwell', font_size_curr))],
    [sg.Text("Voltage: ", key='cur_volts', font=('Rockwell', font_size_curr))],
    [sg.Text("Tilt X: ", key='cur_tilt_x', font=('Rockwell', font_size_curr))],
    [sg.Text("Tilt Y: ", key='cur_tilt_y', font=('Rockwell', font_size_curr))],
    [sg.Text("GPS Latitude: ", key='cur_lat', font=('Rockwell', font_size_curr))],
    [sg.Text("GPS Longitude: ", key='cur_lon', font=('Rockwell', font_size_curr))],
]
third_row = [sg.Frame(layout=misc_info, title='MISC Info', title_color='yellow', font=('Rockwell', 20), border_width=3,
                      size=(300, 300)),
             sg.Txt(" " * 10),
             sg.TabGroup([[sg.Tab('Tilt X & Y', gyro_layout, key='gyro'),
                           sg.Tab('Altitude', altitude_layout, key='altitude'),
                           sg.Tab('Temperature', temp_layout, key='temp'),
                           sg.Tab('Voltage', voltage_layout, key='voltage'), sg.Tab('GPS', gps_layout, key='gps')]],
                         enable_events=True),
             sg.Txt(" " * 10),
             sg.Frame(layout=current_stat_cols, title='Current Payload Values', title_color='yellow',
                      font=('Rockwell', 20), border_width=3)]
fourth_row = [sg.Text(' ' * 15), sg.Button('Save CSV', size=(10, 1)),
              sg.Button('Enable Simulation', key='simEnable', size=(20, 1)),
              sg.Button('Activate Simulation', key='simActivate', size=(20, 1), visible=False)]
commands_row = [sg.Text('Command Bar: '), sg.Input(key='cmdInput'), sg.Button('Send'),
                sg.Button('Enable Backup Mode', key='backupMode')]
command_echo_row = [sg.Text('Command Echo: ', key='echo')]
layout = [[first_row_A], [first_row_B], [second_row], [second_row_B], [sg.Text(" ")], [third_row], [fourth_row],
          [commands_row], [command_echo_row]]

# Get screen size
screen_width, screen_height = sg.Window.get_screen_size()
# Calculate window size based on screen size

# Create the Window
_VARS['window'] = sg.Window('CanSat GUI',
                            layout,
                            finalize=True,
                            resizable=True,
                            location=((screen_width - 1425) * 2, int((screen_height - 725) / 4)),
                            font=("Rockwell", 16),
                            margins=(50, 50),
                            element_justification='center'
                            )


def getSpecificTelemetryData(name):  # Gets specific backup data (temp, alt, etc.) from the backup data
    global yData
    if name == "altitude":
        tempYData = [[], []]
        for i in telemetryData:
            tempYData[0].append(float(i[5]))
            if i[13] == "":
                tempYData[1].append(0.0)
            else:
                tempYData[1].append(float(i[13]))
        yData = np.array(tempYData)  # ALTITUDE
    elif name == 'temp':
        tempYData = []
        for i in telemetryData:
            tempYData.append(float(i[9]))
        yData = np.array(tempYData)  # TEMPERATURE
    elif name == 'voltage':
        tempYData = []
        for i in telemetryData:
            tempYData.append(float(i[11]))
        yData = np.array(tempYData)  # VOLTAGE
    elif name == 'gps':
        tempXData = []
        tempYData = []
        for i in telemetryData:
            tempXData.append(float(i[14]))
            tempYData.append(float(i[15]))
        xData = np.array(tempXData)  # LATITUDE
        yData = np.array(tempYData)  # LONGITUDE
        return xData, yData  # Latitude vs Longitude
    elif name == 'gyro':
        tempYData = [[], []]
        for i in telemetryData:
            tempYData[0].append(float(i[17]))  # X value tilt for gyro
            tempYData[1].append(float(i[18]))  # Y value tile for gyro
        yData = np.array(tempYData)  # GYRO X
    xData = []  # MISSION TIME
    for i in telemetryData:
        xData.append(i[1])
    return xData, yData  # Time versus whatever Y is (not GPS)


def drawChart(name):  # Draws graph
    fig, ax = plt.subplots()
    _VARS[name + 'PltFig'] = fig

    dataXY = getSpecificTelemetryData(name)

    finalX = []  # Stores the x data to plot
    finalY = []  # Store the y data to plot
    finalY2 = []  # Store the y data of the second gyro just in case
    if len(dataXY) > 0 and len(dataXY[0]) > 0 and len(dataXY[1]) > 0:
        iterations = len(dataXY[0]) - 1
        if iterations >= 0:
            if simulationMode:
                _VARS['window']['mode'].update('Mode: S')  # Reset packet count (for simulation)
            else:
                _VARS['window']['mode'].update('Mode: F')  # Reset packet count (for simulation)
            _VARS['window']['state'].update(
                'State: ' + str(telemetryData[iterations][4]))  # Update all of these things for the figure
            _VARS['window']['heat-shield'].update('Heat Shield Deployed: ' + str(telemetryData[iterations][6]))
            _VARS['window']['parachute'].update('Parachute Deployed: ' + str(telemetryData[iterations][7]))
            _VARS['window']['mast'].update('Mast Raised: ' + str(telemetryData[iterations][8]))
            _VARS['window']['echo'].update('Command Echo: ' + str(telemetryData[iterations][-1]))
            # Update all the current values
            _VARS['window']['cur_altitude'].update(f'Altitude: {telemetryData[-1][5]} (m)')
            _VARS['window']['cur_pressure'].update(f'Pressure: {telemetryData[-1][10]} (kPa)')
            _VARS['window']['cur_temp'].update(f'Temperature: {telemetryData[-1][9]} (C)')
            _VARS['window']['cur_volts'].update(f'Voltage: {telemetryData[-1][11]} (V)')
            _VARS['window']['cur_tilt_x'].update(f'Tilt X: {telemetryData[-1][17]}')
            _VARS['window']['cur_tilt_y'].update(f'Tilt Y: {telemetryData[-1][18]}')

            if telemetryData[iterations][16] == "":
                _VARS['window']['sats'].update('GPS Sats: NA', text_color='red')
                _VARS['window']['cur_lat'].update("GPS Latitude: NA ", text_color='red')
                _VARS['window']['cur_lon'].update("GPS Longitude: NA ", text_color='red')
                _VARS['window']['cur_gps_altitude'].update("GPS Altitude: NA m", text_color='red')
                _VARS['window']['gps_mission_time'].update("GPS Mission Time: NA", text_color='red')
            else:
                _VARS['window']['sats'].update(f'GPS Sats: {telemetryData[iterations][16]}', text_color='white')
                _VARS['window']['cur_lat'].update(f'GPS Latitude: {telemetryData[-1][14]}', text_color='white')
                _VARS['window']['cur_lon'].update(f'GPS Longitude: {telemetryData[-1][15]}', text_color='white')
                _VARS['window']['cur_gps_altitude'].update(f'GPS Altitude: {telemetryData[-1][13]} m',
                                                           text_color='white')
                _VARS['window']['gps_mission_time'].update(f'GPS Mission Time: {telemetryData[-1][12]}',
                                                           text_color='white')

            if name != 'gyro' and name != 'altitude':
                for index in range(iterations):
                    finalX.append(dataXY[0][index])  # Add x data in form of datetime.datetime
                    finalY.append(dataXY[1][index])  # Add y data
            else:
                for index in range(iterations):
                    finalX.append(dataXY[0][index])  # Add x data in form of datetime.datetime
                    finalY.append(dataXY[1][0][index])  # Add x tilt or altitude from pressure
                    finalY2.append(dataXY[1][1][index])  # Add y tilt or GPS altitude
            if name != 'gps' and name != 'gyro' and name != 'altitude':
                ax.plot(finalX, finalY, color="blue")  # Plot data colored blue
            elif name == 'gyro':
                line1, = ax.plot(finalX, finalY, color="blue", label='X-Tilt')  # Plot data colored blue
                line2, = ax.plot(finalX, finalY2, color="red", label='Y-Tilt')  # Plot data colored blue
                ax.legend(handles=[line1, line2], loc='center', bbox_to_anchor=(1.025, 1.075))
            elif name == 'altitude':
                line1, = ax.plot(finalX, finalY, color="blue", label='PRESS Alt')  # Plot data colored blue
                line2, = ax.plot(finalX, finalY2, color="red", label='GPS Alt')  # Plot data colored blue
                ax.legend(handles=[line1, line2], loc='center', bbox_to_anchor=(1, 1.075))
            else:
                ax.plot(finalX, finalY, color="blue",
                        linewidth=0.75)  # Make line width smaller for gps since the plot is weird (you'll see)
    # Set axes titles, and labels
    xlabel = 'Time (HH:MM:SS)'
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
    if name == 'voltage':
        ylabel = 'Voltage (V)'
        title = 'Voltage Vs. Time'
    elif name == 'gps':
        ylabel = 'Longitude (degrees)'
        xlabel = 'Latitude (degrees)'  # Overwrite x-label
        title = 'Longitude Vs. Latitude'
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.4f'))
        ax.xaxis.set_major_formatter(FormatStrFormatter('%.4f'))
        plt.yticks(fontsize=9)
        plt.xticks(fontsize=9)
    elif name == 'altitude':
        ylabel = 'Altitude (m)'
        title = 'Altitude Vs. time'
    elif name == 'temp':
        ylabel = 'Temperature (C)'
        title = 'Temperature Vs. time'
    elif name == 'gyro':
        ylabel = 'Degrees'
        title = 'Degrees Vs. Time'
    else:
        title = ""
        ylabel = []
    plt.title(title, fontdict={'size': 16})
    plt.xlabel(xlabel, fontdict={'color': 'black'})  # Set x-label
    plt.ylabel(ylabel, fontdict={'color': 'black'})  # Set y-label

    ax.yaxis.set_major_locator(plt.MaxNLocator(7))  # Maximum of 7 ticks on y-axis
    ax.xaxis.set_major_locator(plt.MaxNLocator(7))  # Maximum of 7 ticks on x-axis

    [t.set_color('black') for t in ax.xaxis.get_ticklines()]  # Make x-axis tick lines and labels black instead of grey
    [t.set_color('black') for t in ax.xaxis.get_ticklabels()]
    [t.set_color('black') for t in ax.yaxis.get_ticklines()]  # Make y-axis tick lines and labels black instead of grey
    [t.set_color('black') for t in ax.yaxis.get_ticklabels()]
    # Draw figure
    _VARS[name + '_agg'] = draw_figure(  #
        _VARS['window'][name + 'Canvas'].TKCanvas, _VARS[name + 'PltFig'])


def updateChart(name):  # Updates graph
    plt.close()
    _VARS[name + '_agg'].get_tk_widget().forget()
    plt.clf()
    plt.cla()
    drawChart(name)


# Draw the initial graphs
figure_names = ['gps', 'altitude', 'temp', 'voltage', 'gyro']
for item in figure_names:
    drawChart(item)

# Event Loop to process "events" and get the "values" of the inputs

"""Interface code to connect with the Xbee"""

hc_bool_states = {
    'N': False,
    'P': True,
}
pc_bool_states = {
    'N': False,
    'C': True,
}
mast_bool_states = {
    'N': False,
    'M': True
}
flight_mode_states = {
    'F': False,
    'S': True
}
states = {
    "LAUNCH_WAIT": 0,
    "ASCENT": 1,
    "ROCKET_SEPARATION": 2,
    "DEC_PROBE_HS": 3,
    "DEC_PROBE_PC": 4,
    "DEC_PROBE_MT": 5,
    "LANDED_WAIT": 6
}

flight_states = {
    "start_payload": False,
    "flight_mode": False,
    "hc_bool": False,
    "pc_bool": False,
    "mast_bool": False,
    "state": 0,
    "packet_count": 0,
    "mission_time": 0

}


# Function to handle incoming data
def handle_data(data, flight_states,
                states, hc_bool_states, mast_bool_states, pc_bool_states, flight_mode_states):
    # Do something with the received data
    # @TODO Figure out start
    teamID = "1071"
    if data.find(teamID, 0, len(teamID)) == -1:
        package_count = flight_states["packet_count"]
        num_states = 0b000000
        num_states |= (flight_states["start_payload"] << 0)
        num_states |= (flight_states["hc_bool"] << 1)
        num_states |= (flight_states["pc_bool"] << 2)
        num_states |= (flight_states["mast_bool"] << 3)
        num_states |= (flight_states["flight_mode"] << 4)
        num_states |= (flight_states["state"] << 5)
        temp_var = flight_states["mission_time"]
        cmd = f"{teamID},5,{temp_var},{num_states},{package_count},"
        ser.write(cmd.encode('utf-8'))
        _VARS['window']['echo'].update('Command Echo: Satellite Ready')
    else:
        shared_data.put(data)
        data_cont = data.split(",")
        # Save necessary flight states and info in
        # case of defect
        try:
            flight_states["start_payload"] = isCanSatON
            flight_states["state"] = states[data_cont[4]]
            flight_states["hc_bool"] = hc_bool_states[data_cont[6]]
            flight_states["pc_bool"] = pc_bool_states[data_cont[7]]
            flight_states["mast_bool"] = mast_bool_states[data_cont[8]]
            flight_states["packet_count"] = data_cont[2]
            flight_states["flight_mode"] = flight_mode_states[data_cont[3]]
            data_cont[1] += ":"
            temp_cont = data_cont[1].split(':')
            flight_states["mission_time"] = int(temp_cont[0]) * 3600 + int(temp_cont[1]) * 60 + int(temp_cont[2])

        except IndexError:
            pass


def read_serial(flight_states, states, hc_bool_states,
                mast_bool_states, pc_bool_states, flight_mode_states):
    while True:
        try:
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8').rstrip()
                # Call the handle_data function to process the received data
                handle_data(data, flight_states, states,
                            hc_bool_states, mast_bool_states,
                            pc_bool_states, flight_mode_states)
        except:
            _VARS['window']['Connect'].update('Connection Failed', button_color='#DA3A3A')


# Configure the serial port
try:
    # Check if the serial port is open
    # =========================================================================================================
    while True:
        event, values = _VARS['window'].read(timeout=10)
        _VARS['window']['time'].update('Mission Time: ' + getTime())

        # GUI Buttons:
        # Close window or click cancel
        if event == sg.WIN_CLOSED or event == 'Close':
            break
        # Send command
        elif event == 'Send' and connected:
            CMD_ECHO = values['cmdInput']
            _VARS['window']['echo'].update('Command Echo: ' + str(
                CMD_ECHO))  # Update the command echo element to display the previously entered command
            _VARS['window']['cmdInput'].update('')  # This resets the input bar to be empty
            try:

                # Enable simulation mode command
                if CMD_ECHO == 'CMD,1071,SIM,ENABLE':
                    _VARS['window']['simEnable'].update('Disable Simulation', button_color='#DA3A3A')
                    _VARS['window']['simActivate'].update(visible=True)
                    simulationMode = False
                    simulationActivation = True
                # Activate simulation mode command
                elif CMD_ECHO == 'CMD,1071,SIM,ACTIVATE':
                    simulationMode = True
                    start = datetime.utcnow().strftime('%H:%M:%S')
                    seconds = 0
                # Disable simulation mode command
                elif CMD_ECHO == 'CMD,1071,SIM,DISABLE':
                    simulationMode = False
                    simulationActivation = False
                    simulationData = []
                    for item in figure_names:  # Reset each of the 4 figures
                        updateChart(item)
                    _VARS['window']['state'].update('State: LAUNCH_WAIT')
                    _VARS['window']['heat-shield'].update('Heat Shield Deployed: N')
                    _VARS['window']['parachute'].update('Parachute Deployed: N')
                    _VARS['window']['mast'].update('Mast Raised: N')
                    _VARS['window']['mode'].update('Mode: F')
                    _VARS['window']['packet_count'].update('Packet Count: 0')
                    _VARS['window']['simActivate'].update(visible=False)
                    _VARS['window']['simEnable'].update('Enable Simulation', button_color='#FFB84D')
                # Send pressure data command
                elif 'CMD,1071,SIMP' in CMD_ECHO:
                    if simulationMode == False or simulationActivation == False:
                        break
                # Calibrate altitude to zero command
                elif CMD_ECHO == 'CMD,1071,CAL':
                    # NOT SURE WHAT TO DO HERE -- CALIBRATE ALTITUDE TO 0 M IN ARDUINO?
                    GPS_ALTITUDE = 0
                    try:
                        for item in figure_names:  # Reset each of the 4 figures
                            updateChart(item)
                    except:
                        pass
                # Power OFF CanSat
                elif CMD_ECHO == 'CMD,1071,CX,OFF':
                    isCanSatON = False
                    _VARS['window']['Power ON'].update('Power ON', button_color='#00b300')
                    saveCSVfile(telemetryData)
                # Power ON CanSat
                elif CMD_ECHO == 'CMD,1071,CX,ON':
                    isCanSatON = True
                    telemetryData = []
                    _VARS['window']['Power ON'].update('Power OFF', button_color='#DA3A3A')
                # Set time
                elif 'CMD,1071,ST' in CMD_ECHO:
                    if 'GPS' in CMD_ECHO:
                        # Set FSW time to the current time read from the GPS module
                        MISSION_TIME = str(datetime.now().strftime("%H:%M:%S"))
                    else:
                        utc_time_pattern = re.compile(r'\b\d{2}:\d{2}:\d{2}\b')
                        utc_times = re.findall(utc_time_pattern, CMD_ECHO)
                        if utc_times:
                            # Set FSW time to the value utc_times
                            MISSION_TIME = str(utc_times[0])
                    print(MISSION_TIME)
                # Send command!
                # print(CMD_ECHO)
                sendXBeeCommand(CMD_ECHO)
            except:
                print("Error transmitting command.")
        # Calibrate
        elif event == 'Calibrate' and connected:  # and after_connection:
            # Window to Calibrate all sensors in Payload
            sg.set_options(font=('Rockwell', 16,))
            sg.theme('UFTheme')  # Add a touch of color
            # All the stuff inside your window.
            mission_time = ['UTC-Now', 'GPS-Time']
            dropDown = sg.Combo(values=mission_time, font=('Arial Bold', 14), expand_x=True, enable_events=True,
                                readonly=True, key='MT')
            layout1 = [[sg.Text('Calibrate All Settings for Payload', auto_size_text=True)],
                       [sg.Text('Mission Time'), dropDown, sg.Button('Set M')],
                       [sg.Text('Altitude Sensor'), sg.Button('Calibrate')],
                       [sg.Button('Open Servos'), sg.Button('Close Servos')],
                       [sg.Button('End Calibration')]]
            should_continue = False
            # Create the Window
            window = sg.Window('Calibration Window',
                               layout1,
                               resizable=True,
                               element_justification='center',
                               finalize=True
                               )
            # Event Loop to process "events" and get the "values" of the inputs
            time_set = False
            altitude_cal = False
            servo_closed = False
            while True:
                event, values = window.read()
                if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
                    break
                elif event == 'Set M':
                    if values['MT'] == 'UTC-Now':
                        temp_curr_time = datetime.utcnow().time().strftime('%H:%M:%S')
                        current_time = temp_curr_time + ':'
                        current_time = current_time.split(":")
                        time_num = int(current_time[0]) * 3600 + int(current_time[1]) * 60 + int(current_time[2])
                        sendXBeeCommand(f'CMD,1071,ST,{time_num}')
                        CMD_ECHO = f'CMD,1071,ST,{temp_curr_time}'
                    else:
                        sendXBeeCommand('CMD,1071,ST,GPS')
                        CMD_ECHO = 'CMD,1071,ST,GPS'
                    time_set = True
                    window['Set M'].update(button_color='#00b300')
                elif event == 'Calibrate':
                    sendXBeeCommand('CAL')
                    CMD_ECHO = 'CMD,1071,CAL'
                    altitude_cal = True
                    window['Calibrate'].update(button_color='#00b300')
                elif event == 'Open Servos':
                    sendXBeeCommand('OPEN')
                    CMD_ECHO = 'CMD,1071,OPEN'
                    servo_closed = False
                    window['Close Servos'].update(button_color='#DA3A3A')
                elif event == 'Close Servos':
                    CMD_ECHO = 'CMD,1071,CLOSE'
                    sendXBeeCommand('CLOSE')
                    servo_closed = True
                    window['Close Servos'].update(button_color='#00b300')
                elif event == 'End Calibration':
                    if time_set and altitude_cal and servo_closed:
                        calibrated = True
                        _VARS['window']['Calibrate'].update('Calibrated', button_color='#00b300')
                        break
                _VARS['window']['echo'].update('Command Echo: ' + str(CMD_ECHO))
            window.close()
        # Power ON / Power OFF
        elif event == 'Power ON' and connected and calibrated:
            isCanSatON = not isCanSatON
            # Power ON CanSat
            if isCanSatON:
                CMD_ECHO = 'CMD,1071,CX,ON'
                _VARS['window']['Power ON'].update('Power OFF', button_color='#DA3A3A')
            # Power OFF CanSat
            else:
                _VARS['window']['Power ON'].update('Power ON', button_color='#00b300')
                CMD_ECHO = 'CMD,1071,CX,OFF'
                saveCSVfile(telemetryData)
            _VARS['window']['echo'].update('Command Echo: ' + str(
                CMD_ECHO))  # Update the command echo element to display the previously entered command
            _VARS['window']['cmdInput'].update('')  # This resets the input bar to be empty
            xbee_sent = False
            try:
                sendXBeeCommand(CMD_ECHO)
                if simulationMode and simulationActivation: time.sleep(2)
            except:
                print("Error transmitting command.")
        # Connect to the serial port
        elif event == 'Connect':
            ports = serial.tools.list_ports.comports()
            port_num = 0
            window_txt = ""
            for i, onePort in enumerate(ports):
                window_txt += str(i) + " " + str(onePort) + "\n"
            sg.set_options(font=('Rockwell', 16,))
            sg.theme('UFTheme')  # Add a touch of color
            # All the stuff inside your window.
            layout1 = [[sg.Text(window_txt, auto_size_text=True)],
                       [sg.Text('Port Number'), sg.InputText()],
                       [sg.Button('Enter'), sg.Button('Cancel')]]
            should_continue = False
            # Create the Window
            window = sg.Window('Select GCS-Port', layout1, resizable=True)
            # Event Loop to process "events" and get the "values" of the inputs
            while True:
                event, values = window.read()
                if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
                    break
                elif event == "Enter":
                    if values[0].isnumeric():
                        port_num = values[0]
                        should_continue = True
                        break
            window.close()
            if should_continue:
                try:
                    ser = serial.Serial(
                        port=ports[int(port_num)].name,
                        # port='/dev/tty.usbserial-D30AXZ1V',  # Update this with the correct serial port of your device
                        baudrate=9600,  # Update this with the correct baud rate of your device
                        timeout=1,  # Timeout value in seconds
                        xonxoff=True
                        # /dev/tty.usb* mac command
                    )
                    if ser.is_open:
                        print('Serial open')
                        # Start the thread to read data from the serial port
                        t = threading.Thread(target=read_serial, args=(flight_states, states,
                                                                       hc_bool_states, mast_bool_states,
                                                                       pc_bool_states, flight_mode_states,))
                        t.daemon = True
                        t.start()
                        connected = True
                        _VARS['window']['Connect'].update('Connected', button_color='#00b300')


                except Exception as e:
                    connected = False
                    _VARS['window']['Connect'].update('Connection Failed', button_color='#DA3A3A')
                    print(e)
        elif event == 'Save CSV' and connected:
            saveCSVfile(telemetryData)

        elif event == 'simActivate' and connected:
            simulationMode = True
            CMD_ECHO = 'CMD,1071,SIM,ACTIVATE'
            _VARS['window']['echo'].update('Command Echo: ' + str(
                CMD_ECHO))  # Update the command echo element to display the previously entered command
            sendXBeeCommand('CMD,1071,SIM,ACTIVATE')
            # _VARS['window']['cmdInput'].update('')  # This resets the input bar to be empty
            # If user enables/disables simulation mode
            _VARS['window']['simEnable'].update('Disable Simulation', button_color='#DA3A3A')
            _VARS['window']['simActivate'].update(visible=False)
        elif event == 'simEnable' and connected:
            if not simulationMode and not simulationActivation:
                CMD_ECHO = 'CMD,1071,SIM,ENABLE'
                sendXBeeCommand('CMD,1071,SIM,ENABLE')
                _VARS['window']['echo'].update('Command Echo: ' + str(
                    CMD_ECHO))  # Update the command echo element to display the previously entered command
                _VARS['window']['cmdInput'].update('')  # This resets the input bar to be empty
                _VARS['window']['simEnable'].update('Simulation Enabled', button_color='#00b300')
                _VARS['window']['simActivate'].update(visible=True)
                simulationMode = False
                simulationActivation = True

            elif simulationMode or simulationActivation:
                CMD_ECHO = 'CMD,1071,SIM,DISABLE'
                _VARS['window']['echo'].update('Command Echo: ' + str(CMD_ECHO))
                # Update the command echo element to display the previously entered command
                _VARS['window']['simEnable'].update('Enable Simulation', button_color='#ffb84d')
                _VARS['window']['cmdInput'].update('')  # This resets the input bar to be empty
                _VARS['window']['simActivate'].update(visible=False)
                simulationMode = False
                simulationActivation = False
                sendXBeeCommand("CMD,1071,SIM,DISABLE")
        elif event == 'backupMode':
            backupMode = not backupMode
            # Enable backup mode
            if backupMode:
                _VARS['window']['backupMode'].update('Disable Backup Mode', button_color='#DA3A3A')
            # Disable backup mode
            else:
                _VARS['window']['backupMode'].update('Enable Backup Mode', button_color='#FFB84D')
            #     for item in figure_names: # Reset each of the 4 figures
            #         updateChart(item)
        else:
            if simulationMode and simulationActivation and not xbee_sent and isCanSatON:
                if simulation_data_count >= len(simulatedPressureData):
                    # Add some more behaviors when disabled
                    sendXBeeCommand("CMD,1071,SIM,DISABLE")
                    _VARS['window']['echo'].update('Pressure Simulation Complete')
                    _VARS['window']['simEnable'].update('Enable Simulation', button_color='#ffb84d')
                    _VARS['window']['cmdInput'].update('')  # This resets the input bar to be empty
                    _VARS['window']['simActivate'].update(visible=False)
                    _VARS['window']['Power ON'].update('Power ON', button_color='#00b300')
                    CMD_ECHO = 'CMD,1071,CX,OFF'
                    saveCSVfile(telemetryData)
                    isCanSatON = False
                    simulationMode = False
                    simulationActivation = False
                    time.sleep(2)
                    sendXBeeCommand('CMD,1071,CX,OFF')

                else:
                    _VARS['window']['echo'].update('Command Echo: ' + str(simulatedPressureData[simulation_data_count]))
                    sendXBeeCommand(simulatedPressureData[simulation_data_count])
                    simulation_data_count += 1
                    xbee_sent = True
                # for simulation mode send a packet and wait for it to come back
            if backupMode and not simulationMode and not simulationActivation:
                if len(backupData) > backup_data_count:
                    telemetryData.append(backupData[backup_data_count])
                    backup_data_count += 1
                    PACKET_COUNT = backup_data_count
                    _VARS['window']['packet_count'].update('Packet Count: ' + str(PACKET_COUNT))  # Update packet count

                    updateChart(values[0])  # Update the chart of the tab that is active, if this fails (it shouldn't) then nothing happens
                    dataReceived = False
                else:
                    pass
            else:
                dataReceived = readXBeeData()

            if dataReceived:
                xbee_sent = False
                PACKET_COUNT = flight_states["packet_count"]
                _VARS['window']['packet_count'].update('Packet Count: ' + str(PACKET_COUNT))  # Update packet count
                try:
                    updateChart(values[
                                    0])  # Update the chart of the tab that is active, if this fails (it shouldn't) then nothing happens
                except:
                    pass
    print('Flight Software Ending')
    _VARS['window'].close()
    sys.exit()
    t.join()
    ser.close()
    # Close the serial port

except Exception as e:
    print(e)
