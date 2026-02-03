#define ANALOG_X_PIN A2 
#define ANALOG_Y_PIN A3 
#define ANALOG_X_CORRECTION 128 
#define ANALOG_Y_CORRECTION 128 

struct analog { 
    short x, y; 
}; 

// forward declarations
byte readAnalogAxisLevel(int pin);
bool isAnalogButtonPressed(int pin);

void setup() 
{ 
    Serial.begin(115200); 
} 

void loop() 
{ 
    analog stick; 

    stick.x = readAnalogAxisLevel(ANALOG_X_PIN) - ANALOG_X_CORRECTION; 
    stick.y = readAnalogAxisLevel(ANALOG_Y_PIN) - ANALOG_Y_CORRECTION; 

    Serial.print("X:"); 
    Serial.println(stick.x); 

    Serial.print("Y:"); 
    Serial.println(stick.y); 

    delay(200); 
} 

byte readAnalogAxisLevel(int pin) 
{ 
    return map(analogRead(pin), 0, 1023, 0, 255); 
} 