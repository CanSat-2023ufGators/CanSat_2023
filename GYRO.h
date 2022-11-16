#pragma once
//#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

class GYRO : public Adafruit_BNO055 { // inheritance
    //private
    Adafruit_BNO055 gyro;
    sensors_event_t orientationData, magnetometerData; 
    double gyro_data[3];
    uint16_t BNO055_SAMPLERATE_DELAY_MS; 
    public:
        GYRO(int32_t sensorID, uint8_t address);
        bool checkSensor();
        double* exportData();
        
};
