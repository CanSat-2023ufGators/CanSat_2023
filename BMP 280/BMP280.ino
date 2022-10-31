#include <BMP280.h> 

BMP280 temperature_meter();
BMP280 pressure_meter(); 

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600); 

}

void loop() {
  // put your main code here, to run repeatedly:
  //call

  pressure_meter.setPres(); //analog read? 
  Serial.print("Pressure: ");
  Serial.println(pressure_meter.getPres());

  temperature_meter.setPres(); //analog read?
  Serial.print("Temperature: ");
  Serial.println(temperature_meter.getTemp()); 

}