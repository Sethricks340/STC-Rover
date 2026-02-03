#define ANALOG_X_PIN A2 
#define ANALOG_Y_PIN A3 

struct analog { 
    float x, y; 
}; 

// forward declarations
float readAnalogAxisLevel(int pin);

void setup() 
{ 
    Serial.begin(115200); 
} 

void loop() 
{ 
    analog stick; 

    stick.x = readAnalogAxisLevel(ANALOG_X_PIN); 
    stick.y = readAnalogAxisLevel(ANALOG_Y_PIN); 

    Serial.print("X:"); 
    Serial.println(stick.x); 

    Serial.print("Y:"); 
    Serial.println(stick.y); 
} 

float readAnalogAxisLevel(int pin)
{
  float raw = analogRead(pin);       // 0 .. 1023
  float scaled = (raw / 1023.0f) * 2.0f - 1.0f;  // scale to -1.0 .. 1.0
  return scaled;
}