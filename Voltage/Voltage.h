#pragma once 
class Voltage{
    //private 
    double referencev; 
    int sample_rate;
    int sum;                    //sum of samples taken
    unsigned char sample_count; //current sample num
    double voltage;             //calculated voltage 
    public:
        Voltage(int sample_rate, double referenceV);
        double getVolts(); 
        void setVolts(double data);
  

};
