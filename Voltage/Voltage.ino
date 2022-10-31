#include "Voltage/Voltage.h"
Voltage voltMeter (10, 5.015); 
void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
 
}

void loop() {
  // put your main code here, to run repeatedly:
  voltMeter.setVolts(analogRead(A2)); 
  Serial.print("Volts:");
  Serial.println(voltMeter.getVolts()); 

}