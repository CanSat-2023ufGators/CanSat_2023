#include <Wire.h>
#include "SparkFunMPL3115A2.h"
#include "Voltage.h"
#include "GYRO.h" 
#define teamID 1073 //Team Id
//for time
/* Useful Constants */
#define MIL_PER_SEC (1000UL) 
#define SECS_PER_MIN  (60UL)
#define SECS_PER_HOUR (3600UL)
#define SECS_PER_DAY  (SECS_PER_HOUR * 24L)

 
/* Useful Macros for getting elapsed time */
#define numberOfMilSeconds(_time_) (_time_ % MIL_PER_SEC) 
#define numberOfSeconds(_time_) (_time_ % SECS_PER_MIN)  
#define numberOfMinutes(_time_) ((_time_ / SECS_PER_MIN) % SECS_PER_MIN) 
#define numberOfHours(_time_) (( _time_% SECS_PER_DAY) / SECS_PER_HOUR) 

//Create an instance of the objects
MPL3115A2 myPressure;
Voltage voltMeter(10, 5.015);
GYRO gyro (55,0x28); 
 
String packet = "";  //for developing packet
int packetCount = 0; 

int timeT = 0;
int currentMil = 0; 

String stateList [10] = {
  "LAUNCH_WAIT",
  "ASCENT",
  "ROCKET_SEPARATION",
  "DESCENT1",
  "PROBE_RELEASE",
  "DESCENT2",
  "PARACHUTE_DEPLOY",
  "DESCENT3",
  "LANDED",
  "LANDED_WAIT"  
};

int currState = 0;
int count = 0; 

char flight_mode[2] = {83, 70};
bool mode = false; //1 for sensors - 0 for simulation 
bool accent = true; 
bool simp = false; 

char hs_deployed[2] = {78, 80}; // P - Heat sheild deployed N -otherwise
bool hs_bool = false ;

char pc_deployed[2] = {78,67}; // C - parachute deployed N -otherwise
bool pc_bool = false ;

char mast_deployed[2] = {78,77}; // M - Heat sheild deployed N -otherwise
bool mast_bool = false ;

float findState(float alt1, float alt2, int &currState, int &count); 

float alt1 = 0; 
float alt2 = 1;

float avgAlt = 0; 

//GYRO Storage
double* gdata; 

//Commands to payload
//CMD,<TEAM_ID>,CX,<ON_OFF>
//CMD,<TEAM_ID>,ST,<UTC_TIME>|GPS  UTC_Time or GPS
//CMD,<TEAM_ID>,SIM,<MODE>
//CMD,<TEAM ID>,SIMP,<PRESSURE>
//CAL - Calibrate Altitude to Zero
//OPTIONAL - Optional Commands

void setup (){
  pinMode(2, OUTPUT);
  // Wait for something that turns it on
  Wire.begin();
  Serial.begin(9600);
  delay(100); 
  Serial.println("Starting...."); 

  // Get sensors online
  //=============================//
  myPressure.begin();
  if (!gyro.checkSensor()){
   Serial.print("Ooops, no BNO055 detected ... Check your wiring or I2C ADDR!");
   //while (1);
  } 
  //=============================//
  //Configure the sensor
  myPressure.setModeAltimeter(); // Measure altitude above sea level in meters
  myPressure.setOversampleRate(7); // Set Oversample to the recommended 128
  const int groundLevel_m = 50;
  delay (1000);
}


void loop() {
  
   if (mode){ // flight mode 
     alt1 = myPressure.readAltitude();
     delay(5);
     alt2 = myPressure.readAltitude();   
   }
   else if (!mode && !simp)  { //simulation 
    if (accent == true && alt1 < 750){
      alt1++;
      alt2++;
    }
    else if (accent == true && alt1 >= 750){
      accent = false;
      alt2 -= 2; 
    }
    else if (accent == false && alt1 > 0){
     alt1--;
     alt2--;
    } 
   } 
   else{
    //pumped preasure data 
   }
   //========================================================
   //Getting data 
   avgAlt = findState(alt1, alt2, currState, count);  // altitude and state
   voltMeter.setVolts(analogRead(A2));  //voltage 
   gdata = gyro.exportData();          // tilt_x, tilt_y, temp
   currentMil =  millis(); 
   timeT += currentMil; 
   //gps stuff
   //========================================================
   // Develop sensor data packet
   packet += String(teamID) + ", ";
   
   packet += String(numberOfHours(timeT/1000)) + ":";
   packet += String(numberOfMinutes(timeT/1000)) + ":"; 
   packet += String(numberOfSeconds(timeT/1000)) + ":" ;
   packet += String(numberOfMilSeconds(timeT)/10) + ", ";  // work on mili
   
   packet += String(packetCount) + ", ";
   packet += String(flight_mode[mode]) + ", " ;
   packet += String(avgAlt) + ", "; 
   packet += String(hs_deployed[hs_bool]) + ", "; 
   packet += String(pc_deployed[pc_bool]) + ", "; 
   packet += String(mast_deployed[mast_bool]) + ", "; 
   //packet += String((*(gdata+2)+myPressure.readTemp())/2) + ", "; // Temp 
   packet += String(*(gdata+2)) + ", "; // Temp 
   packet += String(voltMeter.getVolts()) + ", "; 
   packet += String() + ", "; // GPS_Time
   packet += String() + ", "; // GPS_Altitude 
   packet += String() + ", "; // GPS_Latitude 
   packet += String() + ", "; // GPS_Longitude 
   packet += String() + ", "; // GPS_SATS
   packet += String(*(gdata+0)) + ", "; //Tilt_x
   packet += String(*(gdata+1)) + ", "; //Tilt_y
   packet += String() + ", ["; //CMD_ECHO
   packet += String() + ", ]"; // optional data
 //========================================================
   Serial.println(packet);
   packet = "";
   packetCount++; 
   timeT -= currentMil;  
   //Behaviors 
   
   switch(currState){
         case 0: //LAUNCH_WAIT 
         break; 
        
         case 2://ROCKET_SEPARATION
         break; 
         
         case 4://PROBE_RELEASE
         hs_bool = true; 
         break; 
         
         case 6://PARACHUTE_DEPLOY
         pc_bool = true;
         break;
          
         case 8://LANDED
         mast_bool = true; 
         break; 

         case 9:// "LANDED_WAIT"  
         digitalWrite(2, HIGH);// LED and Sound Device 
         break;

         default:
         //do nothing during accent and descent stages
         break;
      }        
}

float findState(float alt1, float alt2, int &currSate, int &count){
      //finding altitude  
      //for accent and actual value;
      float altDif = (alt2 - alt1); 
      float altAvg = (alt1 + alt2)/2;
      //*********************************//
      //The idea behind this is to check if we should change to the next state//
      //*********************************//
      switch(currState){
         case 0: //LAUNCH_WAIT
         float dataA[2]; 
         if (altDif > 0){ // If difference in alt is + 
          count++;         // add to count
            if (count > 5){
              currState++; //once count has been increasing for 5 straight times change state
              count = 0;
            }
         }
         else count = 0;
          
         break; 
         
         case 1: //ASCENT
         if (altDif < 0){ // If difference in alt is -
          count++;         // add to count
           
            if (count > 5) {
              currState++; //once count has been increasing for 5 straight times change state
              count = 0;
            }
         }
         else count = 0;
         
         break; 
         
         case 2://ROCKET_SEPARATION
         //Rocket Seperation is quick, one  ms only 
         currState++;
         break; 
         
         case 3://DESCENT1
         if (altAvg < 500){ // if altitude is less than 500
          count++;         // add to count
            if (count > 2) {
              currState++; //once count has been increasing for 5 straight times change state
              count = 0;
            }
         }
         else count = 0;
         break; 

         case 4: //PROBE_RELEASE
         currState++; 
         break;
         
         case 5://DESCENT2
         if (altAvg < 200){ // if altitude is less than 200
          count++;         // add to count
            if (count > 5) {
              currState++; //once count has been increasing for 5 straight times change state
              count = 0;
            }
         }
         else count = 0;
         break; 
         
         case 6://PARACHUTE_DEPLOY
         currState++; 
         break; 

         case 7:// DESCENT3
         if (altAvg < 5){ // if altitude is less than 5
          count++;         // add to count
            if (count > 2) {
              currState++; //once count has been increasing for 5 straight times change state
              count = 0;
            }
         }
         else count = 0;
         break;
          
         case 8://LANDED
         currState++;
         break; 

         case 9:// "LANDED_WAIT"  
         break;
      }           
      return altAvg; 

}
