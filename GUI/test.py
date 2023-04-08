data=[]
input = "b'1071,LAUNCH_WAIT,,26,-23.39,,,,20.88,101606.25,0.33,,,,,,,359.94,-1.13,1071,0,1'"
processed = input[input.find('1071'):(input.rfind('1071')-1)]
# Get the command
command = input[input.rfind('1071'):]
if (command[-1] == "'"): command = command[:-1]
# CONVERT COMMAND TO STRING
if (command == "1071,0,1"): command = "CXON"
elif (command == "1071,"): command = "FIXME"
# Add telemetry data to the list
processed = processed.split(',')
processed.append(command)
data.append(processed)
print(processed)