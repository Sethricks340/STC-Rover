#define Pot_PIN A0 

//Variables:
int value;

#define ANALOG_X_PIN A2 
#define ANALOG_Y_PIN A3 

struct analog { 
    float x, y;
    int pot;
}; 

// forward declarations
float readAnalogAxisLevel(int pin);

void setup() 
{ 
  Serial.begin(115200); 
} 

void loop() 
{ 
    analog control; 

    control.x = readAnalogAxisLevel(ANALOG_X_PIN)  * - 1.0f; // Flip x axis
    control.y = readAnalogAxisLevel(ANALOG_Y_PIN); 

    Serial.print("X:"); 
    Serial.println(control.x); 

    Serial.print("Y:"); 
    Serial.println(control.y); 

    control.pot = map(analogRead(Pot_PIN), 0, 1023, 0, 255); //Map value 0-1023 to 0-255 (PWM)
    Serial.print("P:"); 
    Serial.println(control.pot);  
} 

float readAnalogAxisLevel(int pin)
{
  float raw = analogRead(pin);       // 0 .. 1023
  float scaled = (raw / 1023.0f) * 2.0f - 1.0f;  // scale to -1.0 .. 1.0
  return scaled;
}