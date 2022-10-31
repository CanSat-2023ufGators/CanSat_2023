#include "GYRO.h"
GYRO gyro (55,0x28); 
double* gdata; 
void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  if (!gyro.checkSensor()){
   Serial.print("Ooops, no BNO055 detected ... Check your wiring or I2C ADDR!");
   while (1);
  }
  
  delay (1000);
}

void loop() {
  // put your main code here, to run repeatedly:
  gdata = gyro.exportData();
  for (int i = 0; i < 3; i++){
    Serial.print("data:");
    Serial.print(i);
    Serial.println(*(gdata+i));
  }
  
}
