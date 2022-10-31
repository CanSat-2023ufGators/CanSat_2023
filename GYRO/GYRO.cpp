#include "GYRO.h"

GYRO::GYRO(int32_t sensorID, uint8_t address){
    uint16_t BNO055_SAMPLERATE_DELAY_MS = 100;
    this->gyro = Adafruit_BNO055(sensorID, address);
    this-> BNO055_SAMPLERATE_DELAY_MS = 100;
    
}
bool GYRO::checkSensor(){
  return this->gyro.begin(); 
}
double* GYRO::exportData()
{
  this->gyro.getEvent(&this->orientationData, Adafruit_BNO055::VECTOR_EULER );
  //this->gyro.getEvent(&this->magnetometerData, Adafruit_BNO055::VECTOR_MAGNETOMETER);
  this->gyro_data[0] = orientationData.orientation.x;
  this->gyro_data[1] = orientationData.orientation.y;
  this->gyro_data[2] = orientationData.orientation.z;
  return this->gyro_data;
}
