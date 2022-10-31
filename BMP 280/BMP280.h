#pragma once 
#include "Adafruit_BMP280.h"
class BMP280:: public Adafruit_BMP280{
  Adafruit_BMP280 bmp; 
  Adafruit_Sensor *bmp_temp;
  Adafruit_Sensor *bmp_pressure;
  // private 
  public:
    BMP280(); 
    void getPres();
    double setPres();
    void getTemp();
    double setTemp();
}; 