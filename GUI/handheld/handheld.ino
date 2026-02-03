#define ANALOG_X_PIN A2 
#define ANALOG_Y_PIN A3 

int input_start = 0;    // The lowest number of the range input.
int input_end = 255;    // The largest number of the range input.
int output_start = -255; // The lowest number of the range output.
int output_end = 255;  // The largest number of the range output.

struct analog { 
    short x, y; 
}; 

// forward declarations
int readAnalogAxisLevel(int pin);

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

int readAnalogAxisLevel(int pin) 
{ 
    return map(analogRead(pin), 0, 1023, -255, 255); 
} 