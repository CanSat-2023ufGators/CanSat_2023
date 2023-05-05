
#include <Wire.h>
//Pressure
#include <Adafruit_MPL3115A2.h>
//GPS
#include <Adafruit_GPS.h>
#include <SoftwareSerial.h>
//Gyro
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>
//Servos
#include <Servo.h>
//===============Connections Comments===========
//GPS
// Connect the GPS Power pin to 5V
// Connect the GPS Ground pin to ground
// Connect the GPS TX (transmit) pin to Digital 8
// Connect the GPS RX (receive) pin to Digital 7
//MPL3115A2
//Connect the MPL3115A2 Power pin to 3.3V
//Connect the MPL3115A2 Ground pin to ground
//Connect the MPL3115A2 SDA to A4
//Connect the MPL3115A2 SCL to A5
//BNO055
//Connect the BNO055 Power pin to 5V
//Connect the BNO055 Ground pin to ground
//Connect the BNO055 SDA to A4
//Connect the BNO055 SCL to A5
//Camera 
// Connect power to 5V (red)
// Connect ground to GNV (black)
// Connect trigger to Digital pin 5 (green or white)
//Buzzer & LED
// Connect power to Digital pin 2
// Connect GND to
// LED* Connect a resistor from cathode to DP 2
//Voltage divider 
//Connection: Battery (+) -> 1M Resitor (measureA2) -> 100k Resistor -> GND
//===========================================

//Create instance of objects 
//Altimeter
Adafruit_MPL3115A2 sense_pressure_alt; // I2C
//GYRO
Adafruit_BNO055 gyro = Adafruit_BNO055(55); 
//GPS
SoftwareSerial newSerial(8, 7); 
Adafruit_GPS GPS(&newSerial);
//Servos 
Servo mast_servo;
Servo pc_servo;

//================Defines==================== 
#define teamID 1071

/* Useful Constants */
#define SECS_PER_MIN  (60UL)
#define SECS_PER_HOUR (3600UL)
#define SECS_PER_DAY  (SECS_PER_HOUR * 24L)

#define Bit(x) 1 << x

/* Useful Macros for getting elapsed time */
#define numberOfSeconds(_time_) (_time_ % SECS_PER_MIN)  
#define numberOfMinutes(_time_) ((_time_ / SECS_PER_MIN) % SECS_PER_MIN) 
#define numberOfHours(_time_) (( _time_% SECS_PER_DAY) / SECS_PER_HOUR) 

//Digital Pin MISC 
#define locationDevices 2
#define camera_loc 5
#define mast_motor 11
#define pc_motor 10
#define nichrome 9

//Pressure Eq for simulation
#define pressure_To_Alt(_pressure_) (44330 * pressure_To_Alt2(_pressure_))
#define pressure_To_Alt2(_pressure_) (1-pressure_To_Alt3(_pressure_))
#define pressure_To_Alt3(_pressure_) (pow(float(_pressure_)/101325, 1/5.255))

//Rate macro for transmission protocol
#define TX_rate 500
//Persistance macro
#define persist 3

//================Important Vars ===========================
const char* const stateList [7] = {
  "LAUNCH_WAIT",
  "ASCENT",
  "ROCKET_SEPARATION", 
  "DEC_PROBE_HS",
  "DEC_PROBE_PC",
  "DEC_PROBE_MT",
  "LANDED_WAIT"
};
//used to select the state
uint8_t state = 0;
//State persistance count to make sure we want to go into that state
byte state_persist = 0;
//used to start the setup for the payload
bool start_payload = false;
//Sim Enabled
bool sim_enable = false; 
//Sim Activated
bool sim_activated = false;
//Calibration for Altimeter
float calibrated_altitude = 0.0;
//String to contain data
String payload_data;
//Packet count 
uint16_t packet_count = 0; 
//Flight pressur var 
float flight_press; 
//Flight altitudes 
float canSat_altitude1 = 0;
float canSat_altitude2 = 0;


// P - Heat sheild deployed N -otherwise 
const char hs_deployed[2] = {78, 80}; 
bool hs_bool = false ;
 // C - parachute deployed N -otherwise
const char pc_deployed[2] = {78,67};
bool pc_bool = false ;
// M - Heat sheild deployed N -otherwise
const char mast_deployed[2]  = {78,77}; 
bool mast_bool = false ;
//Flight Mode
const char flight_mode[2] = {70, 83};
bool flight_bool = false; //1 for sensors - 0 for simulation 
//String for the CMD ECHO
String cmd_echo;
//Unisgned 32 bit variable to keep track of time
uint32_t mission_time = 0; 
//==============Function Prototypes=========
float getVolts(); 
uint32_t command_parsing (Adafruit_MPL3115A2 &sense_pressure_alt);
uint32_t gpsData(Adafruit_GPS &GPS, String &gpsDataPacket, bool onlyTime);
void camera_trigger();
uint32_t decode_time (String time_stamp);
//============Command Prototypes==============//
uint32_t timer = millis();
void setup(){
  Wire.begin();      // Join i2c buss
  Serial.begin(9600);// Start serial for output
  //=========Sensor Init============
  //Pressure
  if (!sense_pressure_alt.begin()) {
    Serial.print("ERR-1");
}
  //Gyro 
  if(!gyro.begin()){
    Serial.print("ERR-2");
  }
  //GPS.begin(9600);
  //newSerial.end();
  //For LED and sound device
   pinMode(locationDevices,OUTPUT);
   //Camera setup 
   pinMode(camera_loc,OUTPUT);
   analogWrite(camera_loc, 167);
//   //Motors
  mast_servo.attach(mast_motor);
  pc_servo.attach(pc_motor); 
  //Nichrome
  pinMode(nichrome, OUTPUT);

  //===========Sensor Config ==========
  // STD SLP = 1013.26 hPa
  //Altimeter
  sense_pressure_alt.setMode(MPL3115A2_BAROMETER);
  sense_pressure_alt.setSeaPressure(1013.26);
  //Gyro
  gyro.setExtCrystalUse(true);
  //GPS
  GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCGGA);
  // Set the update rate
  GPS.sendCommand(PMTK_SET_NMEA_UPDATE_1HZ);   // 1 Hz update rate


  
  //=============Flight Software init===========
  while(!Serial);                    //Wait for Serial to turn on correctly 
  
  while(Serial.available() == 0){    
    //Request for GS to return a command toset up states. 
    if (millis() - timer >= 2000) {
      Serial.print("-1"); 
      timer = millis(); 
    }
  }
  command_parsing(sense_pressure_alt); 
  
  
  while(!start_payload){
     // All sensors have been setup, but will not begin to transmit until the
     //On command is given.
    if (Serial.available() > 0){
        command_parsing (sense_pressure_alt); 
     }
     
   }   
   mast_servo.attach(4);
  pc_servo.attach(4);
         
}
void loop() {
   
  /*
   * Decide  where altitude data will come from
  */
   if (sim_enable && sim_activated){
      flight_bool = true; 
      while(Serial.available() == 0); 
      flight_press = command_parsing(sense_pressure_alt);  
      if (flight_press <= 0) return;
      
   }
   else if (Serial.available() > 0 ) {
    command_parsing(sense_pressure_alt);
   }
   else flight_press = sense_pressure_alt.getPressure() * 100;
   
   if(!start_payload) return; 
   
    canSat_altitude2 = canSat_altitude1;
    canSat_altitude1 = pressure_To_Alt(flight_press) - calibrated_altitude;
    byte altDif = canSat_altitude2 - canSat_altitude1; //might have to change
    //==========================State Behaviors for Flight=================/
       
       switch(state){
        case 0://Launch Wait
        if (canSat_altitude1 > 5){
            state++;
        }
        break; 
       
        case 1://Accent
        if (altDif > 0){ // If difference in alt is -
          state_persist++;         // add to count
            if (state_persist > persist) {
              state++; //once count has been increasing for 5 straight times change state
              state_persist = 0;
            }
         }
         else state_persist = 0;
        break;
        
        case 2://Rocket Seperation
        if (state_persist > persist && canSat_altitude1 > 500) {
          state++;
          state_persist = 0;
          camera_trigger();
        }
        state_persist ++; 
        
        break;

        case 3://Decent1
        if (canSat_altitude1 < 500){ // if altitude is less than 500
          state_persist++;         // add to count
            if (state_persist > persist) {
              hs_bool = true;
              digitalWrite(nichrome, HIGH);
               //Case dependent
              state++; //once count has been increasing for 5 straight times change state
              state_persist = 0;
            }
         }
         else state_persist = 0;
        break;
         
        case 4://Decent 2
        if (canSat_altitude1 < 200){ // if altitude is less than 200
          state_persist++;         // add to count
            if (state_persist > persist) {
              pc_bool = true;
              digitalWrite(nichrome, LOW);
              pc_servo.attach(pc_motor);
              pc_servo.write(90);
              state++; //once count has been increasing for 5 straight times change state
              state_persist = 0;
            }
         }
        break;

        case 5://Decent 3
        if (canSat_altitude1 < 5 || altDif  < 1 || altDif > -1 ){ // if altitude is less than 5
          state_persist++;         // add to count
            if (state_persist > persist) {
              mast_bool = true;
              mast_servo.attach(mast_motor);
              mast_servo.write(180);
              state++; //once count has been increasing for 5 straight times change state
              state_persist = 0;
              camera_trigger();
            }
         }
         else state_persist = 0;
        break;

        case 6://Landed
        digitalWrite(locationDevices, HIGH); //LED and SOUND DEVICE

        break;
       //=======================================================================//
       }
    if (millis() - timer >= TX_rate) {
       sensors_event_t gyro_event;
        gyro.getEvent(&gyro_event);

        payload_data = String(teamID) + ',';           //Team ID
        uint32_t temp_time  = mission_time + (millis()/1000);
        
        uint8_t temp_timeholder = numberOfHours(temp_time);
        if (temp_timeholder < 10) payload_data += '0';
        payload_data += String(temp_timeholder) + ':';    //Hour
        
        temp_timeholder = numberOfMinutes(temp_time);
        if (temp_timeholder < 10) payload_data += '0';
        payload_data += String(temp_timeholder) + ':';   // Minute

        temp_timeholder = numberOfSeconds(temp_time);
        if (temp_timeholder < 10) payload_data += '0';
        payload_data += String(temp_timeholder) + ',';  // Seconds Mission time
        
        payload_data += String(packet_count++) + ',';   //Packet Count
        payload_data += String(flight_mode[flight_bool]) + ',';  //CanSat Mode
        payload_data += String(stateList[state]) + ',';   
        payload_data += String(round(canSat_altitude1*10)/10.0) + ',';  //Altitude
        payload_data += String(hs_deployed[hs_bool]) + ',';   //HS_
        payload_data += String(pc_deployed[pc_bool]) + ',';   //PC
        payload_data += String(mast_deployed[mast_bool]) + ',';   //Mast
        payload_data += \
        String(round(sense_pressure_alt.getTemperature()* 10)/10.0) + ',';   //Temperature
        payload_data += String(round(flight_press/100)/10.0) + ',';
        payload_data += String(round(getVolts()*10)/10.0) + ',';
        gpsData(GPS, payload_data, false); 
        payload_data += String(gyro_event.orientation.x) + ',';
        payload_data += String(gyro_event.orientation.y) + ',';
        payload_data += cmd_echo;
        Serial.print(payload_data);
        timer = millis();
      }
}

//============================================================================//
/*
   * getVolts() returns float value of the voltage 
   * Description: Uses analogRead to read the voltage coming from 
   * an analog port and runs its through an equation using parrallel 
   * resistors
   * Connection: Battery (+) -> 1M Resitor (measureA2) -> 100k Resistor -> GND
   */
float getVolts(){
  
  //====Any changes should be made here to the function=========//
  #define A 1024.0
  #define B 11.132 
  #define sample_rate 5
  #define referenceV 5.015
  //============================================================//
  byte sample_count = 0;
  uint16_t sum = 0; 
  
  while(sample_count < sample_rate){
    sum += analogRead(A2);
    sample_count++;  
  }
  return (((sum / sample_rate) * referenceV) / A )*B;
}

//============================================================================//
/*
 * gpsData(Adafruit_GPS &GPS, String &gpsDataPacket) return a parsed string with Time, Lattitude, Longitude, Satellite count
 * Description: Using Software Serial the gps will continue to read characters from the GPS until an entire NEMA sentence is read. Doing it this way ensures we have both sentences needed for all of or information.
 this funcition will also double as a way to get the time for initialization  
 * Variables:
 *We pass in the GPS object to get our data
 *We pass in the String packet container to modify it directly
 *Returns the GPS given time in uint32_t to be decoded later. 
 */ 
 uint32_t gpsData(Adafruit_GPS &GPS, String &gpsDataPacket, bool onlyTime){
   GPS.begin(9600);
    bool finish = false;
    bool first_sentence = false;
    while(!finish){
      char c = GPS.read();
      if (GPS.newNMEAreceived()) {
        if (GPS.parse(GPS.lastNMEA())){
          if (first_sentence == true) finish = true;
          first_sentence = true;
        } 
      }
    }   
     newSerial.end();
        if (GPS.fix){
          if (GPS.hour < 10) { gpsDataPacket += '0'; }
          gpsDataPacket += String(GPS.hour) + ":";
          if (GPS.minute < 10) { gpsDataPacket += '0'; }
          gpsDataPacket += String(GPS.minute) + ":";
          if (GPS.seconds < 10) { gpsDataPacket += '0'; }
          gpsDataPacket += String(GPS.seconds) + ",";
          
          //For Initializarion 
          if (onlyTime)
          return \
          GPS.hour * SECS_PER_HOUR + GPS.minute * SECS_PER_MIN + GPS.seconds;

          gpsDataPacket += String(GPS.altitude) + ", ";
          gpsDataPacket += String(GPS.latitude);
          gpsDataPacket += String(GPS.lat) + ", "; 
          gpsDataPacket += String(GPS.longitude); 
          gpsDataPacket += String(GPS.lon) + ", ";
          gpsDataPacket += String(GPS.satellites) + ", ";
        }
        else 
          gpsDataPacket +=  ",,,,,";
    return 0;
  }
/*
 * command parsing to manipulate the incoming data from the xbee.
 * 
 */
uint32_t command_parsing (Adafruit_MPL3115A2 &sense_pressure_alt) {
  cmd_echo = Serial.readString();
  uint32_t command_handler[5];
  uint8_t count = 0;
  String temp;
  for (int i = 0; i < cmd_echo.length(); i++){
    //ADD a comman or colon to end a transmission
    if(cmd_echo[i] == ',' || cmd_echo[i] == ':' ){
      command_handler[count] = temp.toInt(); 
      temp = "";
      count ++; 
      
    }
    else {
      temp += cmd_echo[i];
    }
  }
 
  if(command_handler[0] != teamID) return-1; //Wrong ID
  //CX
  if(command_handler[1] == 0)  start_payload = bool(command_handler[2]);  
  //ST    
  else if (command_handler[1] == 1){
    if (command_handler[2] == -1){
      //GPS Time
      mission_time = gpsData(GPS, temp, true);
    }
    else{
      //sent as a 32 bit uint
      mission_time = command_handler[2];
    }
  }
  //SIM
  else if (command_handler[1] == 2){
    if(command_handler[2] == 0) {
        sim_activated = false; 
        sim_enable = false;
        flight_bool = false; 
      }
      else if (command_handler[2] == 1) sim_activated = true; 
      else if (command_handler[2] == 2) sim_enable = true;
      else return -1;
  }
  //SIMP
  else if (command_handler[1] == 3) return command_handler[2];
  //CAL
  else if (command_handler[1] == 4) calibrated_altitude = pressure_To_Alt(sense_pressure_alt.getPressure()*100);

  else if (command_handler[1] == 5) {
    //Add flight elevation
    start_payload = (command_handler[3] & Bit(0));
    hs_bool = (command_handler[3] & Bit(1));
    pc_bool = (command_handler[3] & Bit(2));
    mast_bool = (command_handler[3] & Bit(3));
    flight_bool = (command_handler[3] & Bit(4));
    state = (command_handler[3] >> 5);  
    mission_time = command_handler[2];
    packet_count = command_handler[4];
    
  }
  else if(command_handler[1] == 6){ // open all servos
    pc_servo.write(90);
  }
  else if(command_handler[1] == 7){ // close all servos
    pc_servo.write(0);
    mast_servo.write(0);
    
  }
  return 0; //Correct sequence
  }

void camera_trigger(){
  
  analogWrite(locationDevices,0);
  delay(500);
  analogWrite(locationDevices, 167);
}
