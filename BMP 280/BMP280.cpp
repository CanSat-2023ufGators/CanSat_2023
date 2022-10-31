// might need to fix this
#include <CanSat_2023/BMP 280/BMP280.h> 
// #include <Wire.h>
// #include <SPI.h>
// #include <Adafruit_BMP280.h>
// from example  

// почиму  -> why 

BMP280::BMP280(){
     this->bmp = Adafruit_BMP280(); // use I2C interface
     &temp = this->bmp.getTemperatureSensor();
     &pressure = this->bmp.getPressureSensor();
    // is this it?     
}

double BMP280::getPres(){
    return this -> pressure;
}

void BMP280::setPres(){
    pressure -> getEvent(&pressure_event); 
}

double BMP280::getTemp(){
    return this -> temp; 
}

void BMP280::setTemp(){
    temp -> getEvent(&temp_event);
}

// circuit (I2C): 
// SCL to SCK
// SDA to SDI


// from the BMP example in Arduino IDE:

//#include <Wire.h>
//#include <SPI.h>
//#include <Adafruit_BMP280.h>

//Adafruit_BMP280 bmp; // use I2C interface
//Adafruit_Sensor *bmp_temp = bmp.getTemperatureSensor();
//Adafruit_Sensor *bmp_pressure = bmp.getPressureSensor();

//  sensors_event_t temp_event, pressure_event;
//  bmp_temp->getEvent(&temp_event);
//  bmp_pressure->getEvent(&pressure_event);
  
//  Serial.print(F("Temperature = "));
//  Serial.print(temp_event.temperature);
//  Serial.println(" *C");

//  Serial.print(F("Pressure = "));
//  Serial.print(pressure_event.pressure);
//  Serial.println(" hPa");

//  Serial.println();
//  delay(2000);
//}