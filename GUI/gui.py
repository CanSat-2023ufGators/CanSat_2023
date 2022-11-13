import PySimpleGUI as sg
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from datetime import datetime
import matplotlib.dates as mdates

# Creates custom look and feel
sg.LOOK_AND_FEEL_TABLE['UFTheme'] = {'BACKGROUND': '#383535',
                                        'TEXT': '#F9F9FB',
                                        'INPUT': '#F9F9FB',
                                        'TEXT_INPUT': '#000000',
                                        'SCROLL': '#99CC99',
                                        'BUTTON': ('#F9F9FB', '#ffb84d'),
                                        'PROGRESS': ('#D1826B', '#CC8019'),
                                        'BORDER': 1, 'SLIDER_DEPTH': 0,
                                        'PROGRESS_DEPTH': 0, }


# Switch to use your newly created theme
sg.theme('UFTheme')


#Read the simulation file
dataFrame = pd.read_excel('simulation.xlsx')
header = dataFrame.columns.tolist()

#Convert the data frame to a list of lists
simulationData = []
for i in header:
    simulationData.append(dataFrame[i].tolist()) #data is a list of lists

#Get the current time
def getTime():
    return time.strftime("%H:%M:%S", time.gmtime())

#Vars constants
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
        
dataSize = 1000 #Used for the fake data plots

# Theme for pyplot
plt.style.use('Solarize_Light2')

#Draws a figure to be saved to the window's layout
def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

#Global variables
TEAM_ID = '1071'
MISSION_TIME = 0
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
CMD_ECHO = 'none'

simulationMode = False #Toggle T/F if user activates SIM mode in GUI
simulationActivation = False #Toggle T/F if user enables/disables SIM mode in GUI
start = 0 #Start time value (gets initialized in the While loop when sim mode is enabled)
seconds = 1 #How many seconds have passed (for sim mode)
recalibrate = False #After you turn off simulation, recalibrate graphs
#Color

#Figure tab layouts
gps_layout = [[sg.Canvas(key='gpsCanvas', background_color='#FDF6E3', size = (100,100))]]
altitude_layout = [[sg.Canvas(key='altitudeCanvas', background_color='#FDF6E3')]]
temp_layout = [[sg.Canvas(key='tempCanvas', background_color='#FDF6E3')]]
voltage_layout = [[sg.Canvas(key='voltageCanvas', background_color='#FDF6E3')]]


# spacer1 = '                         '
# spacer2 = '                               '
spacer3 = '                                                                                                           '
spacer4 = '                                   '
stateSpacing = { #This is the spacing for the second row (with the states that change)
    'LAUNCH_WAIT' : ' '*32,
    'ASCENT' : ' '*18,
    'ROCKET_SEPERATION' : ' '*47,
    'DESCENT' : ' '*21,
    'HS_RELEASE' : ' '*26,
    'LANDED' : ' '*19
}
packetSpacing = [' '*25, ' '*28, ' '*30] #This is the spacing for the first row (with the packet counts that change)
cmdSpacing = { #This is the spacing for the seventh row (with the command echos that change)
    #NEED TO UPDATE THESE VALUES -- TOO MUCH WORK I THINK. DO WE EVEN NEED COMMAND ECHO??
    #DIFFERENT TYPES OF COMMANDS:
    #CXON, CXOFF, SThh:mm:ss, STGPS, SIMENABLE, SIMDISABLE, SIMACTIVATE, SIMP101325, CAL
    #CMD,1071,CX,ON
    #CMD,1071,ST,hh:mm:ss
    #CMD,1071,ST,GPS
    #CMD,1071,SIM,ENABLE
    #CMD,1071,SIM,DISABLE
    #CMD,1071,SIM,ACTIVATE
    #CMD,1071,SIMP,101325
    #CMD,1071,CAL
    '' : ' '*107,
    'CXON' : ' '*95,
    'ST' : ' '*100,
    #the more spacing, the further left it goes
    'SIMENABLE' : ' '*122,
    'SIMDISABLE' : ' '*125,
    'SIMACTIVATE' : ' '*128,
    'SIMP' : ' '*95,
    'CAL' : ' '*92
}

#Row layouts
first_row = [[sg.Text(f'{packetSpacing[0]}     Team ID: '+ TEAM_ID, key = 'id'), sg.Text('Packet Count: ' + str(PACKET_COUNT), key = 'packet_count'), sg.Text('Mission Time: ' + getTime(), key='time'), sg.Button('Connect', size = (8,1), button_color='#00b300'), sg.Button('Start'), sg.Button('Calibrate'), sg.Button('CLOSE', button_color='#DA3A3A')]]
second_row = [sg.Text(f'{stateSpacing["LAUNCH_WAIT"]}Mode: ' + str(MODE), key = 'mode'), sg.Text('State: ' + str(STATE), key = 'state'), sg.Text('Heat Shield Deployed: ' + HS_DEPLOYED, key = 'heatshield'), sg.Text('Parachute Deployed: ' + PC_DEPLOYED, key = 'parachute'), sg.Text('Mast Raised: ' + MAST_RAISED, key = 'mast')]
third_row = [sg.TabGroup([[sg.Tab('GPS', gps_layout, key='gps'), sg.Tab('Altitude', altitude_layout, key = 'altitude'), sg.Tab('Temperature', temp_layout, key = 'temp'), sg.Tab('Voltage', voltage_layout, key = 'voltage')]], enable_events=True)]
fourth_row= [sg.Button('Simulation Enable', key = 'simEnable', size = (20,1)), sg.Button('Simulation Activate', key = 'simActivate', size = (20,1), visible = False)]
fifth_row = [sg.Button('Save CSV', size = (20,1))]
sixth_row = [sg.Text(f'{packetSpacing[0]}Command Bar: '), sg.Input(key = 'cmdInput'), sg.Button('Send'), sg.Text(f'{spacer4}')]
seventh_row = [sg.Text('Command Echo: ', key = 'echo'), sg.Text(f'{cmdSpacing[""]}                    ', key = 'cmdSpace')]
layout = [[first_row],
          [second_row],
          [third_row],
          [fourth_row],
          [fifth_row],
          [sixth_row],
          [seventh_row]
        ]




# Create the Window
_VARS['window'] = sg.Window('CanSat GUI',
                            layout,
                            finalize=True,
                            resizable=True,
                            location=(100, 100),
                            font = ("Rockwell", 13),
                            element_justification="c")

#Makes the GUI open slightly larger than it normally would
_VARS['window'].maximize()

# Plotting Helper Functions
def makeSynthData(): #Creates fake data (eventually delete this function once we get the live data with packets working)
    xData = np.random.randint(100, size=dataSize)
    yData = np.linspace(0, dataSize, num=dataSize, dtype=int)
    return (xData, yData)

def makeSimulationData(name):  #Creates the data from the simulation file
    if(name == "altitude"):
        yData = np.array(simulationData[5]) #ALTITUDE
    elif(name == 'temp'):
        yData = np.array(simulationData[9]) #TEMPERATURE
    elif(name == 'voltage'):
        yData = np.array(simulationData[10]) #VOLTAGE
    elif(name == 'gps'):
        xData = np.array(simulationData[13]) #LATITUDE
        yData = np.array(simulationData[14]) #LONGITUDE
        return (xData, yData) #Latitude vs Longitude
    xData = [] #MISSION TIME
    for i in simulationData[1]:
        xData.append(datetime.combine(datetime.today(), i))
    return (xData, yData) #Time versus whatever Y is (not GPS)

def drawChart(name): #Draws the charts
    fig, ax=plt.subplots()
    _VARS[name + 'PltFig'] = fig
    if(simulationMode == True): #If simulation mode is enabled
        dataXY = makeSimulationData(name)
        if name != 'gps': #Format the x-axis for all figures NOT gps
            yearss_fmt = mdates.DateFormatter('%M:%S')
            ax.xaxis.set_major_formatter(yearss_fmt)
        finalX = [] #Stores the x data to plot
        finalY = [] #Store the y data to plot
        if seconds + 1 > len(dataXY[0]) - 1:  #Iterations is the max value of number of rows in the file
            iterations = len(dataXY[0]) - 1
        else:
            iterations = seconds + 1 #Iterations is the number of seconds
        _VARS['window']['mode'].update(f'{stateSpacing[str(simulationData[4][iterations])]}Mode: S') #Reset packet count (for simulation)
        _VARS['window']['state'].update('State: ' + str(simulationData[4][iterations])) #Update all of these things for the figure
        _VARS['window']['heatshield'].update('Heat Shield Deployed: ' + str(simulationData[6][iterations]))
        _VARS['window']['parachute'].update('Parachute Deployed: ' + str(simulationData[7][iterations]))
        _VARS['window']['mast'].update('Mast Raised: ' + str(simulationData[8][iterations]))
        _VARS['window']['echo'].update('Command Echo: ' + str(simulationData[18][iterations]))
        for index in range(iterations):
            finalX.append(dataXY[0][index]) #Add x data in form of datetime.datetime
            finalY.append(dataXY[1][index]) #Add y data
            if name != 'gps':
                ax.plot(finalX, finalY, color = "blue") #Plot data colored blue
            else:
                ax.plot(finalX, finalY, color = "blue", linewidth = 0.75) #Make line width smaller for gps since the plot is weird (you'll see)
    else:
        dataXY = makeSynthData() #If it's not in simulation mode -- get random data
        ax.plot(dataXY[0], dataXY[1], '.k')
    plt.xlabel('Time (min : sec)') #Set x-label
    if name == 'voltage':
        yl = 'Voltage (V)'
    elif name == 'gps':
        yl = 'Longitude (degrees)'
        plt.xlabel('Latitude (degrees)') #Overwrite x-label
    elif name == 'altitude':
        yl = 'Altitude (m)'
    elif name == 'temp':
        yl = 'Temperature (C)'
    plt.ylabel(yl) #Set y-label
    _VARS[name + '_agg'] = draw_figure( #Draw figure
        _VARS['window'][name + 'Canvas'].TKCanvas, _VARS[name + 'PltFig'])

def updateChart(name): #Updates chart (basically clears and removes everything from the old one then redraws it)
    plt.close()
    _VARS[name + '_agg'].get_tk_widget().forget()
    plt.clf()
    plt.cla()
    drawChart(name)

#Draw the figures initially
figure_names = ['gps', 'altitude', 'temp', 'voltage']
for item in figure_names:
    drawChart(item)


# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = _VARS['window'].read(timeout = 10)
    _VARS['window']['time'].update('Mission Time: ' + getTime()) #Update time every time the GUI refreshes
    if simulationMode == True: #If we're in simulation mode
        _VARS['window']['simActivate'].update(visible = True)
        if (datetime.now() - start).seconds == seconds:         
            #These adjust the spacing to account for packet counts of 1, 2, and 3 digits long   
            if seconds == 0:
                _VARS['window']['id'].update(f'{packetSpacing[0]}     Team ID: '+ TEAM_ID) #Reset packet count (for simulation)
            elif seconds == 10:
                _VARS['window']['id'].update(f'{packetSpacing[1]}     Team ID: '+ TEAM_ID) #Reset packet count (for simulation)
            elif seconds == 100:
                _VARS['window']['id'].update(f'{packetSpacing[2]}     Team ID: '+ TEAM_ID) #Reset packet count (for simulation)

            if seconds == 1 or seconds % 10 == 0:       #If its the first second of simulation or every 10 seconds, update the graphs so it doesnt have the random data anymore
                _VARS['window']['packet_count'].update('Packet Count: ' + str(seconds)) #Reset packet count (for simulation)
                for item in figure_names: #Update each of the 4 figures
                    updateChart(item) 
            elif seconds < 120:            #For 120 seconds (each data point in the sim file), update the graph of the current tab
                _VARS['window']['packet_count'].update('Packet Count: ' + str(seconds)) #Update packet count
                try:
                    updateChart(values[0]) #Update the chart of the tab that is active, if this fails (it shouldn't) then nothing happens
                except:pass
            elif seconds == 120:  #After 120 seconds, update all of the graphs (in the updateChart code they'll be constant graphs now)
                _VARS['window']['packet_count'].update('Packet Count: 120') #Update packet count
                for item in figure_names: #Update each of the 4 figures
                    updateChart(item)
            seconds += 1         
    elif recalibrate == True: #Recalibrate the charts after simulation mode is turned off
        for item in figure_names: #Update each of the 4 figures
            updateChart(item)     
        recalibrate = False  #Turn off calibration

    if event == sg.WIN_CLOSED or event == 'CLOSE': #If user closes window or clicks cancel
        break
    elif event == 'simActivate':
        simulationMode = True #If simulationMode is false, then make it true. Vise versa.
        start = datetime.now()
        seconds = 0
    elif event == 'simEnable': #If user clicks the simulation button
        if not simulationMode and not simulationActivation:
            _VARS['window']['simEnable'].update('Simulation Disable', button_color='#DA3A3A')
            _VARS['window']['simActivate'].update(visible = True)
            simulationMode = False
            simulationActivation = True
        elif simulationMode or simulationActivation:
            recalibrate = True #If user leaves simulation mode, we have to recalibrate the graphs to random data
            simulationMode = False
            simulationActivation = False
            _VARS['window']['state'].update('State: LAUNCH_WAIT') 
            _VARS['window']['heatshield'].update('Heat Shield Deployed: N')
            _VARS['window']['parachute'].update('Parachute Deployed: N')
            _VARS['window']['mast'].update('Mast Raised: N')
            _VARS['window']['echo'].update('Command Echo: ')
            _VARS['window']['mode'].update(f'{stateSpacing["LAUNCH_WAIT"]}Mode: F')
            _VARS['window']['packet_count'].update('Packet Count: 0') 
            _VARS['window']['simActivate'].update(visible = False)
            _VARS['window']['simEnable'].update('Simulation Enable', button_color='#FFB84D')
    elif event == 'Send':        #If user clicks send button, store the string input typed in the input bar to variable CMD_ECHO
        CMD_ECHO = values['cmdInput']
        _VARS['window']['echo'].update('Command Echo: ' + str(CMD_ECHO)) #Update the command echo element to display the previously entered command
        _VARS['window']['cmdInput'].update('')  #This resets the input bar to be empty
        try:
            _VARS['window']['cmdSpace'].update(f'{cmdSpacing[CMD_ECHO]}                    ')
        except:pass
    elif event == 'Calibrate':   #Eventually change this so the figures update every packet count increase
        try:
            updateChart(values[0]) #Update the chart of the tab that is active, if this fails (it shouldn't) then nothing happens
        except:pass

_VARS['window'].close()