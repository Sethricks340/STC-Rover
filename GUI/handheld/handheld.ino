
#define ANALOG_X_PIN A2 
#define ANALOG_Y_PIN A3 
#define BUTTON_PIN A4

struct analog { 
    // float x, y;
    float x;
    float y;
    int dime;  // Turn on a dime
    int reverse;
}; 

// forward declarations
float readAnalogAxisLevel(int pin);

void setup() 
{ 
  Serial.begin(115200); 
  pinMode(BUTTON_PIN, INPUT_PULLUP);
} 

void loop() 
{ 

    // Serial.println(analogRead(ANALOG_X_PIN)); // Debug
    // Serial.println(analogRead(ANALOG_Y_PIN)); // Debug
    // Serial.println(digitalRead(BUTTON_PIN)); // Debug

    analog control; 

    control.x = readAnalogAxisLevel(ANALOG_X_PIN)  * - 1.0f; // Flip x axis
    Serial.print("X:"); 
    Serial.println(control.x); 

    control.y = readAnalogAxisLevel(ANALOG_Y_PIN); 
    Serial.print("Y:"); 
    Serial.println(control.y);

    control.reverse = (control.y >= 0) ? 0: 1;
    Serial.print("R:"); 
    Serial.println(control.reverse);  

    control.dime = !digitalRead(BUTTON_PIN);
    Serial.print("D:"); 
    Serial.println(control.dime);  
    delay(50);
} 

float readAnalogAxisLevel(int pin)
{
  float raw = analogRead(pin);       // 0 .. 1023
  float scaled = (raw / 1023.0f) * 2.0f - 1.0f;  // scale to -1.0 .. 1.0
  return scaled;
}