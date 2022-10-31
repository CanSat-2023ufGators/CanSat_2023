#include "Voltage.h"

Voltage::Voltage(int sample_rate, double referenceV){
    this->referencev =  referenceV; 
    this->sample_rate = sample_rate;
    this->sum = 0; 
    this->sample_count = 0; 
    this->voltage =  0; //thing being returned
}
double Voltage::getVolts(){
    return this->voltage; 
}
void Voltage::setVolts(double data){
     // take a number of analog samples and add them up
    while (this->sample_count < this->sample_rate) {
        this->sum += data;  //analogRead(A2);
        this->sample_count++;
        int c = 0;
        while (c!=10) c++;
    }
    // calculate the voltage
    // use 5.0 for a 5.0V ADC reference voltage
    this->voltage = ((double)sum / (double)this->sample_rate * this->referencev) / 1024.0;
    // send voltage for display on Serial Monitor
    // voltage multiplied by 11 when using voltage divider that
    // divides by 11. 11.132 is the calibrated voltage divide
    // value
    this->sample_count = 0;
    this->sum = 0;
    this->voltage = this->voltage * 11.132;
    //Battery (+) -> 1M Resitor (measureA2) -> 100k Resistor -> GND
}


