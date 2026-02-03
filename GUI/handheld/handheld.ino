#define ANALOG_X_PIN A2 
#define ANALOG_Y_PIN A3 
#define ANALOG_X_CORRECTION 128 
#define ANALOG_Y_CORRECTION 128 

// Source - https://stackoverflow.com/q/5731863
// Posted by Joe, modified by community. See post 'Timeline' for change history
// Retrieved 2026-02-03, License - CC BY-SA 4.0

int input_start = 0;    // The lowest number of the range input.
int input_end = 255;    // The largest number of the range input.
int output_start = -255; // The lowest number of the range output.
int output_end = 255;  // The largest number of the range output.

// int input = 127; // Input value.
// int output = 0;

// Source - https://stackoverflow.com/a/5732390
// Posted by Alok Singhal
// Retrieved 2026-02-03, License - CC BY-SA 3.0




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

    // stick.x = readAnalogAxisLevel(ANALOG_X_PIN) - ANALOG_X_CORRECTION; 
    // stick.y = readAnalogAxisLevel(ANALOG_Y_PIN) - ANALOG_Y_CORRECTION; 

    // stick.x = readAnalogAxisLevel(ANALOG_X_PIN); 
    // stick.y = readAnalogAxisLevel(ANALOG_Y_PIN); 

    stick.x = output_start + ((output_end - output_start) / (input_end - input_start)) * (readAnalogAxisLevel(ANALOG_X_PIN) - input_start);
    stick.y = output_start + ((output_end - output_start) / (input_end - input_start)) * (readAnalogAxisLevel(ANALOG_Y_PIN) - input_start);

    Serial.print("X:"); 
    Serial.println(stick.x); 

    Serial.print("Y:"); 
    Serial.println(stick.y); 
} 

byte readAnalogAxisLevel(int pin) 
{ 
    return map(analogRead(pin), 0, 1023, 0, 255); 
} 