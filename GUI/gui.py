import PySimpleGUI as sg
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FormatStrFormatter
import pandas as pd
from datetime import datetime
import matplotlib.dates as mdates
import csv
import serial.tools.list_ports
import re

def saveCSVfile(data): # Saves telemetry data to CSV file
    header = ['TEAM_ID', 'MISSION_TIME', 'PACKET_COUNT', 'MODE', 'STATE', 'ALTITUDE', 'HS_DEPLOYED', 'PC_DEPLOYED', 'MAST_RAISED', 'TEMPERATURE', 'VOLTAGE', 'GPS_TIME', 'GPS_ALTITUDE', 'GPS_LATITUDE', 'GPS_LONGITUDE', 'GPS_SATS', 'TILT_X', 'TILT_Y', 'CMD_ECHO']
    with open('Team_' + TEAM_ID+ '.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data)
def readSimulationData(): # Reads simulation pressure data
    simulatedPressureData = []
    f = open("cansat_2023_simp.txt", "r")
    simulatedPressureData = []
    for line in f:
        if ("CMD,$,SIMP," in line):
            simulatedPressureData.append(line[:-1].replace("$","1071"))
    return simulatedPressureData   
def readBackupData(): # Reads backup data
    backupData = []
    with open ('backup_data.csv') as f:
        reader = csv.reader(f)
        for item in reader:
            tempData = []
            for data in item[:-1]:
                tempData.append(data)
            backupData.append(tempData)
    return backupData  
def getSpecificBackupData(name):  # Gets specific backup data (temp, alt, etc) from the backup data
    if(name == "altitude"):
        tempYData = []
        for i in backupData[1:]:
            tempYData.append(float(i[5]))
        yData = np.array(tempYData) #ALTITUDE
    elif(name == 'temp'):
        tempYData = []
        for i in backupData[1:]:
            tempYData.append(float(i[9]))
        yData = np.array(tempYData) #TEMPERATURE
    elif(name == 'voltage'):
        tempYData = []
        for i in backupData[1:]:
            tempYData.append(float(i[10]))
        yData = np.array(tempYData) #VOLTAGE
    elif(name == 'gps'):
        tempXData = []
        tempYData = []
        for i in backupData[1:]:
            tempXData.append(float(i[13]))
            tempYData.append(float(i[14]))
        xData = np.array(tempXData) #LATITUDE
        yData = np.array(tempYData) #LONGITUDE
        return (xData, yData) #Latitude vs Longitude
    xData = [] #MISSION TIME
    for i in backupData[1:]:
        time_object = datetime.strptime(i[1][:-3], '%H:%M:%S').time()
        xData.append(datetime.combine(datetime.today(), time_object))
    return (xData, yData) #Time versus whatever Y is (not GPS)
def getSpecificSimulationData(name):  # Gets specific simulation data (temp, alt, etc) from the simulation data
    if(name == "altitude"):
        tempYData = []
        for i in simulationData[1:]:
            tempYData.append(float(i[5]))
        yData = np.array(tempYData) #ALTITUDE
    elif(name == 'temp'):
        tempYData = []
        for i in simulationData[1:]:
            tempYData.append(float(i[9]))
        yData = np.array(tempYData) #TEMPERATURE
    elif(name == 'voltage'):
        tempYData = []
        for i in simulationData[1:]:
            tempYData.append(float(i[10]))
        yData = np.array(tempYData) #VOLTAGE
    elif(name == 'gps'):
        tempXData = []
        tempYData = []
        for i in simulationData[1:]:
            tempXData.append(float(i[13]))
            tempYData.append(float(i[14]))
        xData = np.array(tempXData) #LATITUDE
        yData = np.array(tempYData) #LONGITUDE
        return (xData, yData) #Latitude vs Longitude
    xData = [] #MISSION TIME
    for i in simulationData[1:]:
        time_object = datetime.strptime(i[1][:-3], '%H:%M:%S').time()
        xData.append(datetime.combine(datetime.today(), time_object))
    return (xData, yData) #Time versus whatever Y is (not GPS)

def getTime(): # Get the current time
    return time.strftime("%H:%M:%S", time.localtime())
def draw_figure(canvas, figure): # Draws a figure to be saved to the window's layout
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

#Global variables
telemetryData = [] # Stores all telemetry data (list of lists)
simulationData = [] # Stores all simulation data (list of lists)
backupData = readBackupData() # Stores the backup data (read from a file)
simulatedPressureData = readSimulationData() # Stores the simulated pressure data (read from a file)
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
simulationMode = False # Toggle T/F if user activates SIM mode in GUI
simulationActivation = False # Toggle T/F if user enables/disables SIM mode in GUI
recalibrate = False # After you turn off simulation, recalibrate graphs
start = 0 # Start time value (gets initialized in the while loop when sim mode is enabled)
seconds = 1 # How many seconds have passed (for sim mode)
backupMode = False # Backup data mode

# Serial port set up
ports = serial.tools.list_ports.comports()
serialInst = serial.Serial()
portsList = []
portVar = None
# # Select which port to connect to
# for onePort in ports:
#     print(onePort)
# portVar = input("Enter the port (e.g. \"COM11\"): ")

# # Initialize serial object thing
serialInst.baudrate = 9600
serialInst.timeout = 0 # Try 1?
# serialInst.port = portVar
# try:
#     serialInst.open()
# except:
#     print("Error opening the port. Telemetry will not work.")
#     pass

def sendXBeeCommand(command): # Send command
    try:
        serialInst.write(command.encode('utf-8'))
        time.sleep(1)
    except:
        print("Error transmitting command.")
def addXBeeInput(input, data): # Takes input (string) and appends it to data (list of lists)
    input = input.split(',')
    tempLine = []
    for item in input:
        tempLine.append(item)
    data.append(tempLine)
    return data
def readXBeeData(): # Read data from serial port
    if (serialInst.is_open):
        try:
            data = serialInst.readline().strip() #maybe add .decode() before strip
            if data:
                # print(data)
                processedData = data[data.find('1071'):(data.rfind('1071')-1)]
                # Get the command
                command = data[data.rfind('1071'):]
                if (command[-1] == "'"): command = command[:-1]
                # CONVERT COMMAND TO STRING
                if (command == "1071,0,1"): command = "CXON"
                elif (command == "1071,"): command = "FIXME"
                # ADD STUFF ^^
                # Add telemetry data to the list
                processedData = processedData.split(',')
                processedData.append(command)
                print(processedData)
                if (simulationMode == True):
                    simulationData.append(processedData)
                elif (backupMode == True):
                    return
                else:
                    telemetryData.append(processedData) 
        except:pass

# Create and swwitch to custom look and feel
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
         }
plt.style.use('Solarize_Light2') # Theme for pyplot

#Figure tab layouts
gps_layout = [[sg.Canvas(key='gpsCanvas', background_color='#FDF6E3', size = (100,100))]]
altitude_layout = [[sg.Canvas(key='altitudeCanvas', background_color='#FDF6E3')]]
temp_layout = [[sg.Canvas(key='tempCanvas', background_color='#FDF6E3')]]
voltage_layout = [[sg.Canvas(key='voltageCanvas', background_color='#FDF6E3')]]

#Row layouts
first_row = [[sg.Text('Team ID: '+ TEAM_ID, key = 'id'), sg.Text('Packet Count: ' + str(PACKET_COUNT), key = 'packet_count'), sg.Text('Mission Time: ' + getTime(), key='time'), sg.Button('Connect'), sg.Button('Power ON', button_color='#00b300'), sg.Button('Calibrate'), sg.Button('Close', button_color='#DA3A3A')]]
second_row = [sg.Text('Mode: ' + str(MODE), key = 'mode'), sg.Text('State: ' + str(STATE), key = 'state'), sg.Text('Heat Shield Deployed: ' + HS_DEPLOYED, key = 'heatshield'), sg.Text('Parachute Deployed: ' + PC_DEPLOYED, key = 'parachute'), sg.Text('Mast Raised: ' + MAST_RAISED, key = 'mast')]
third_row = [sg.Text(' '*15), sg.TabGroup([[sg.Tab('GPS', gps_layout, key='gps'), sg.Tab('Altitude', altitude_layout, key = 'altitude'), sg.Tab('Temperature', temp_layout, key = 'temp'), sg.Tab('Voltage', voltage_layout, key = 'voltage')]], enable_events=True)]
fourth_row= [sg.Text(' '*15), sg.Button('Save CSV', size = (10,1)), sg.Button('Enable Simulation', key = 'simEnable', size = (20,1)), sg.Button('Activate Simulation', key = 'simActivate', size = (20,1), visible = False)]
commands_row = [sg.Text('Command Bar: '), sg.Input(key = 'cmdInput'), sg.Button('Send'), sg.Button('Enable Backup Mode', key = 'backupMode')]
command_echo_row = [sg.Text('Command Echo: ', key = 'echo')]
layout = [[first_row], [second_row], [third_row], [fourth_row], [commands_row], [command_echo_row]]

# Create the Window
_VARS['window'] = sg.Window('CanSat GUI',
                            layout,
                            finalize=True,
                            resizable=True,
                            location=(100, 100),
                            font = ("Rockwell", 13),
                            margins=(300,0))

def drawChart(name): # Draws graph
    fig, ax=plt.subplots()
    _VARS[name + 'PltFig'] = fig

    # If backup data mode is enabled
    if (backupMode == True): 
        dataXY = getSpecificBackupData(name)
        if name != 'gps': # Format the x-axis for all figures NOT gps
            yearss_fmt = mdates.DateFormatter('%H:%M:%S')
            ax.xaxis.set_major_formatter(yearss_fmt)
        finalX = [] # Stores the x data to plot
        finalY = [] # Store the y data to plot
        if seconds + 1 > len(dataXY[0]) - 1:  # Iterations is the max value of number of rows in the file
            iterations = len(dataXY[0]) - 1
        else:
            iterations = seconds + 1 # Iterations is the number of seconds
        _VARS['window']['mode'].update('Mode: F') # Reset packet count (for simulation)
        _VARS['window']['state'].update('State: ' + str(backupData[iterations][4])) # Update all of these things for the figure
        _VARS['window']['heatshield'].update('Heat Shield Deployed: ' + str(backupData[iterations][6]))
        _VARS['window']['parachute'].update('Parachute Deployed: ' + str(backupData[iterations][7]))
        _VARS['window']['mast'].update('Mast Raised: ' + str(backupData[iterations][8]))
        _VARS['window']['echo'].update('Command Echo: ' + str(backupData[iterations][18]))

        for index in range(iterations):
            finalX.append(dataXY[0][index]) # Add x data in form of datetime.datetime
            finalY.append(dataXY[1][index]) # Add y data
            if name != 'gps':
                ax.plot(finalX, finalY, color = "blue") # Plot data colored blue
            else:
                ax.plot(finalX, finalY, color = "blue", linewidth = 0.75) # Make line width smaller for gps since the plot is weird (you'll see)
    
    # If simulation mode is enabled
    elif (simulationMode == True):
        dataXY = getSpecificSimulationData(name)
        if name != 'gps': # Format the x-axis for all figures NOT gps
            yearss_fmt = mdates.DateFormatter('%H:%M:%S')
            ax.xaxis.set_major_formatter(yearss_fmt)
        finalX = [] # Stores the x data to plot
        finalY = [] # Store the y data to plot
        if seconds + 1 > len(dataXY[0]) - 1:  # Iterations is the max value of number of rows in the file
            iterations = len(dataXY[0]) - 1
        else:
            iterations = seconds + 1 # Iterations is the number of seconds
        _VARS['window']['mode'].update('Mode: S') # Reset packet count (for simulation)
        _VARS['window']['state'].update('State: ' + str(simulationData[iterations][4])) # Update all of these things for the figure
        _VARS['window']['heatshield'].update('Heat Shield Deployed: ' + str(simulationData[iterations][6]))
        _VARS['window']['parachute'].update('Parachute Deployed: ' + str(simulationData[iterations][7]))
        _VARS['window']['mast'].update('Mast Raised: ' + str(simulationData[iterations][8]))
        _VARS['window']['echo'].update('Command Echo: ' + str(simulationData[iterations][18]))

        for index in range(iterations):
            finalX.append(dataXY[0][index]) # Add x data in form of datetime.datetime
            finalY.append(dataXY[1][index]) # Add y data
            if name != 'gps':
                ax.plot(finalX, finalY, color = "blue") # Plot data colored blue
            else:
                ax.plot(finalX, finalY, color = "blue", linewidth = 0.75) # Make line width smaller for gps since the plot is weird (you'll see)
    
    # Set axes titles, and labels
    xlabel = 'Time (min : sec)'
    if name == 'voltage':
        ylabel = 'Voltage (V)'
        title = 'Voltage versus time'
    elif name == 'gps':
        ylabel = 'Longitude (degrees)'
        xlabel = 'Latitude (degrees)' #Overwrite x-label
        title = 'Longitude versus latitude'
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
        ax.xaxis.set_major_formatter(FormatStrFormatter('%.3f'))
        plt.yticks(fontsize = 9)
        plt.xticks(fontsize = 9)
    elif name == 'altitude':
        ylabel = 'Altitude (m)'
        title = 'Altitude versus time'
    elif name == 'temp':
        ylabel = 'Temperature (C)'
        title = 'Temperature versus time'
    plt.title(title, fontdict={'size': 16})
    plt.xlabel(xlabel, fontdict={'color': 'black'}) # Set x-label
    plt.ylabel(ylabel, fontdict={'color': 'black'}) # Set y-label

    ax.yaxis.set_major_locator(plt.MaxNLocator(7)) # Maximum of 7 ticks on y-axis
    ax.xaxis.set_major_locator(plt.MaxNLocator(7)) # Maximum of 7 ticks on x-axis

    [t.set_color('black') for t in ax.xaxis.get_ticklines()] # Make x-axis tick lines and labels black instead of grey
    [t.set_color('black') for t in ax.xaxis.get_ticklabels()]
    [t.set_color('black') for t in ax.yaxis.get_ticklines()] # Make y-axis tick lines and labels black instead of grey
    [t.set_color('black') for t in ax.yaxis.get_ticklabels()]
    # Draw figure
    _VARS[name + '_agg'] = draw_figure( #
        _VARS['window'][name + 'Canvas'].TKCanvas, _VARS[name + 'PltFig'])
def updateChart(name): # Updates graph
    plt.close()
    _VARS[name + '_agg'].get_tk_widget().forget()
    plt.clf()
    plt.cla()
    drawChart(name)

# Draw the initial graphs
figure_names = ['gps', 'altitude', 'temp', 'voltage']
for item in figure_names:
    drawChart(item)

# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = _VARS['window'].read(timeout = 10)
    _VARS['window']['time'].update('Mission Time: ' + getTime()) 

# GUI Buttons:
    # Close window or click cancel
    if event == sg.WIN_CLOSED or event == 'Close': 
        break
    # Send command
    elif event == 'Send': 
        CMD_ECHO = values['cmdInput']
        _VARS['window']['echo'].update('Command Echo: ' + str(CMD_ECHO)) # Update the command echo element to display the previously entered command
        _VARS['window']['cmdInput'].update('')  # This resets the input bar to be empty
        try:
            if serialInst.is_open:
                # Enable simulation mode command
                if (CMD_ECHO == 'CMD,1071,SIM,ENABLE'):
                    _VARS['window']['simEnable'].update('Disable Simulation', button_color='#DA3A3A')
                    _VARS['window']['simActivate'].update(visible = True)
                    simulationMode = False
                    simulationActivation = True
                # Activate simulation mode command
                elif (CMD_ECHO == 'CMD,1071,SIM,ACTIVATE'):
                    simulationMode = True
                    start = datetime.now()
                    seconds = 0
                # Disable simulation mode command
                elif (CMD_ECHO == 'CMD,1071,SIM,DISABLE'):
                    simulationMode = False
                    simulationActivation = False
                    simulationData = []
                    for item in figure_names: # Reset each of the 4 figures
                        updateChart(item) 
                    _VARS['window']['state'].update('State: LAUNCH_WAIT') 
                    _VARS['window']['heatshield'].update('Heat Shield Deployed: N')
                    _VARS['window']['parachute'].update('Parachute Deployed: N')
                    _VARS['window']['mast'].update('Mast Raised: N')
                    _VARS['window']['mode'].update('Mode: F')
                    _VARS['window']['packet_count'].update('Packet Count: 0') 
                    _VARS['window']['simActivate'].update(visible = False)
                    _VARS['window']['simEnable'].update('Enable Simulation', button_color='#FFB84D')
                # Send pressure data command
                elif ('CMD,1071,SIMP' in CMD_ECHO):
                    if (simulationMode == False or simulationActivation == False):
                        break
                # Calibrate altitude to zero command
                elif (CMD_ECHO == 'CMD,1071,CAL'):
                    # NOT SURE WHAT TO DO HERE -- CALIBRATE ALTITUDE TO 0 M IN ARDUINO?
                    GPS_ALTITUDE = 0
                    try:
                        for item in figure_names: # Reset each of the 4 figures
                            updateChart(item) 
                    except:pass
                # Power OFF CanSat
                elif (CMD_ECHO == 'CMD,1071,CX,OFF'):
                    isCanSatON = False
                    _VARS['window']['Power ON'].update('Power ON', button_color='#00b300')
                    saveCSVfile(telemetryData)
                # Power ON CanSat
                elif (CMD_ECHO == 'CMD,1071,CX,ON'):
                    isCanSatON = True
                    telemetryData = []
                    _VARS['window']['Power ON'].update('Power OFF', button_color='#DA3A3A')
                # Set time
                elif ('CMD,1071,ST' in CMD_ECHO):
                    if ('GPS' in CMD_ECHO):
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
                sendXBeeCommand(CMD_ECHO)
                time.sleep(1)
            else:
                print("Serial port is not open.")
        except:
            print("Error transmitting command.")
    # Calibrate
    elif event == 'Calibrate': 
        GPS_ALTITUDE = 0
        CMD_ECHO = 'CMD,1071,CAL'
        _VARS['window']['echo'].update('Command Echo: ' + str(CMD_ECHO)) # Update the command echo element to display the previously entered command
        _VARS['window']['cmdInput'].update('')  # This resets the input bar to be empty
        try:
            for item in figure_names: # Reset each of the 4 figures
                updateChart(item) 
        except:pass
    # Power ON / Power OFF
    elif event == 'Power ON':
        isCanSatON = not isCanSatON
        # Power ON CanSat
        if (isCanSatON):
            CMD_ECHO = 'CMD,1071,CX,ON'
            _VARS['window']['Power ON'].update('Power OFF', button_color='#DA3A3A')
        # Power OFF CanSat
        else:
            _VARS['window']['Power ON'].update('Power ON', button_color='#00b300')
            CMD_ECHO = 'CMD,1071,CX,OFF'
            saveCSVfile(telemetryData)
        _VARS['window']['echo'].update('Command Echo: ' + str(CMD_ECHO)) # Update the command echo element to display the previously entered command
        _VARS['window']['cmdInput'].update('')  # This resets the input bar to be empty
        try:
            if serialInst.is_open:
                sendXBeeCommand(CMD_ECHO)
                time.sleep(1)
            else:
                print("Serial port is not open.")
        except:
            print("Error transmitting command.")
    # Connect to the serial port
    elif event == 'Connect':
        # Select which port to connect to
        for onePort in ports:
            print(onePort)
        serialInst.port = input("Enter the port (e.g. \"COM4\"): ")
        try:
            serialInst.open()
            print("Connected to port.")
        except:
            print("Error opening the port. Telemetry will not work.")
            pass
    # Save telemetry data to CSV file
    elif event == 'Save CSV':
        saveCSVfile(telemetryData)

# Simulation Mode:
    # If simulation mode is activated AND enabled
    if simulationMode == True and simulationActivation == True:
         if (datetime.now() - start).seconds == seconds: # Every time a second passes 
            try:
                _VARS['window']['echo'].update('Command Echo: ' + str(simulatedPressureData[seconds])) #Update the command echo element to display the previously entered command
                if serialInst.is_open:
                    sendXBeeCommand(simulatedPressureData[seconds])
                    # MAYBE EDIT THIS
                    time.sleep(1)
                    readXBeeData() 
                else:
                    print("Serial port is not open. " + simulatedPressureData[seconds])
            except:
                print("All simulated pressure data has been transmitted. Ending simulation mode.")
                simulationMode = False
            seconds += 1    
    # If user activates simulation mode
    if event == 'simActivate': 
        simulationMode = True
        CMD_ECHO = 'CMD,1071,SIM,ACTIVATE'
        _VARS['window']['echo'].update('Command Echo: ' + str(CMD_ECHO)) # Update the command echo element to display the previously entered command
        _VARS['window']['cmdInput'].update('')  # This resets the input bar to be empty
        start = datetime.now()
        seconds = 0
    # If user enables/disables simulation mode
    elif event == 'simEnable': 
        if not simulationMode and not simulationActivation:
            CMD_ECHO = 'CMD,1071,SIM,ENABLE'
            _VARS['window']['echo'].update('Command Echo: ' + str(CMD_ECHO)) # Update the command echo element to display the previously entered command
            _VARS['window']['cmdInput'].update('')  # This resets the input bar to be empty
            _VARS['window']['simEnable'].update('Disable Simulation', button_color='#DA3A3A')
            _VARS['window']['simActivate'].update(visible = True)
            simulationMode = False
            simulationActivation = True
        elif simulationMode or simulationActivation:
            simulationData = []
            CMD_ECHO = 'CMD,1071,SIM,DISABLE'
            _VARS['window']['echo'].update('Command Echo: ' + str(CMD_ECHO)) # Update the command echo element to display the previously entered command
            _VARS['window']['cmdInput'].update('')  # This resets the input bar to be empty
            simulationMode = False
            simulationActivation = False
            for item in figure_names: # Reset each of the 4 figures
                updateChart(item) 
            _VARS['window']['state'].update('State: LAUNCH_WAIT') 
            _VARS['window']['heatshield'].update('Heat Shield Deployed: N')
            _VARS['window']['parachute'].update('Parachute Deployed: N')
            _VARS['window']['mast'].update('Mast Raised: N')
            _VARS['window']['mode'].update('Mode: F')
            _VARS['window']['packet_count'].update('Packet Count: 0') 
            _VARS['window']['simActivate'].update(visible = False)
            _VARS['window']['simEnable'].update('Enable Simulation', button_color='#FFB84D')

# Backup Data Mode:
    # If backup mode is active
    if backupMode == True: 
        # _VARS['window']['simActivate'].update(visible = True)
        if (datetime.now() - start).seconds == seconds: # Every time a second passes 
            if seconds == 1 or seconds % 10 == 0 and seconds < len(backupData): # If it's the first second of simulation or every 10 seconds, update all of the graphs
                _VARS['window']['packet_count'].update('Packet Count: ' + str(seconds)) # Reset packet count (for simulation)
                for item in figure_names: # Update each of the 4 figures
                    updateChart(item) 
            elif seconds < len(backupData) - 1:            # For each data packet in the backup data, update the graph of the current tab
                _VARS['window']['packet_count'].update('Packet Count: ' + str(seconds)) # Update packet count
                try:
                    updateChart(values[0]) # Update the chart of the tab that is active, if this fails (it shouldn't) then nothing happens
                except:pass
            elif seconds == len(backupData) - 1:  # After each packet, update all of the graphs (in the updateChart code they'll be constant graphs now)
                _VARS['window']['packet_count'].update('Packet Count: ' + str(seconds)) # Update packet count
                for item in figure_names: # Update each of the 4 figures
                    updateChart(item)
            seconds += 1  
    # If user presses backup data mode button, then toggle backup mode
    if event == 'backupMode':
        backupMode = not backupMode
        # Enable backup mode
        if (backupMode):
            _VARS['window']['backupMode'].update('Disable Backup Mode', button_color='#DA3A3A')
        # Disable backup mode
        else:
            _VARS['window']['backupMode'].update('Enable Backup Mode', button_color='#FFB84D')
            _VARS['window']['state'].update('State: LAUNCH_WAIT') 
            _VARS['window']['heatshield'].update('Heat Shield Deployed: N')
            _VARS['window']['parachute'].update('Parachute Deployed: N')
            _VARS['window']['mast'].update('Mast Raised: N')
            _VARS['window']['echo'].update('Command Echo: ')
            _VARS['window']['mode'].update('Mode: F')
            _VARS['window']['packet_count'].update('Packet Count: 0') 
            for item in figure_names: # Reset each of the 4 figures
                updateChart(item)   
        start = datetime.now()
        seconds = 0        

# MAYBE EDIT THIS
    try:
        time.sleep(1)
        if (serialInst.is_open):
            if (serialInst.in_waiting):
                readXBeeData()
    except:pass
# EDIT ABOVE

_VARS['window'].close()