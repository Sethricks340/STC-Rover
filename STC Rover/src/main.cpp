// TODO: If GUI connection lost, keeps state of last request!
//      Might need to update to TCP or WebSocket for constant connection status

#include <WiFi.h>
#include <Arduino.h>

const int IN1 = 19;
const int IN2 = 18;
const int IN3 = 25;
const int IN4 = 26;

const int enableA = 21;
const int enableB = 27;

const int freq = 5000;
const int channelA = 0;
const int channelB = 1;
const int resolution = 8;

const char* ssid = "Threat Level Midnight";
const char* password = "cowabunga2!!";

// Pick an IP outside your router's DHCP range
IPAddress local_IP(192,168,0,50);  
IPAddress gateway(192,168,0,1);    
IPAddress subnet(255,255,255,0);   
IPAddress dns(8,8,8,8);      

WiFiServer server(80);

int ledPin = 2;  // built-in LED

void motor_on(int number, int pwm){
  if (number){
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
    ledcWrite(channelB, pwm); 
    // ledcWrite(channelB, 255); 
  }
  else {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    ledcWrite(channelA, pwm); 
    // ledcWrite(channelA, 255); 
  }
}

void motor_off(int number){
  if (number){
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, LOW);
    ledcWrite(channelB, 0);
  }
  else {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
    ledcWrite(channelA, 0);
  }
}

void setup() {
  Serial.begin(115200);

  ledcSetup(channelA, freq, resolution);
  ledcAttachPin(enableA, channelA);

  ledcSetup(channelB, freq, resolution);
  ledcAttachPin(enableB, channelB);

  pinMode(ledPin, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  // Set static IP
  if (!WiFi.config(local_IP, gateway, subnet, dns)) {
    Serial.println("STA Failed to configure");
  }

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.print("Connected. IP address: ");
  Serial.println(WiFi.localIP());

  server.begin();
}

void loop() {
  WiFiClient client = server.available();
  if (!client) return;

  String req = client.readStringUntil('\r');
  req.trim();
  client.flush();

// Get Request
int idx;
if ((idx = req.indexOf("/motor/0/on/")) != -1) {
    // Extract everything after "/motor/0/on/"
    String speedStr = req.substring(idx + String("/motor/0/on/").length());
    speedStr.trim();               // remove any trailing \r, \n, spaces
    int speed = speedStr.toInt();  // convert to integer
    Serial.printf("Motor 0 Speed: %d\n", speed); // Debug
    motor_on(0, speed);
}

if ((idx = req.indexOf("/motor/1/on/")) != -1) {
    String speedStr = req.substring(idx + String("/motor/1/on/").length());
    speedStr.trim();
    int speed = speedStr.toInt();
    Serial.printf("Motor 1 Speed: %d\n", speed);
    motor_on(1, speed);
}

// Turn motors off (no speed needed)
if (req.indexOf("/motor/0/off") != -1) motor_off(0);
if (req.indexOf("/motor/1/off") != -1) motor_off(1);


  // Reply
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: text/plain");
  client.println();
  client.print("LED: "); client.println(digitalRead(ledPin) ? "ON" : "OFF");

  client.stop();
}






// Minimal Websocket Example:
/*
#include <WiFi.h>
#include <ESPAsyncWebServer.h>

const char* ssid = "Threat Level Midnight";
const char* password = "cowabunga2!!";

AsyncWebServer server(80);
AsyncWebSocket ws("/ws");  // endpoint

void handleWebSocketMessage(void *arg, uint8_t *data, size_t len) {
    // data is raw bytes from GUI
    data[len] = 0;
    String msg = (char*)data;
    Serial.println("Received: " + msg);

    // Example: motor/0/on/128
    if (msg.startsWith("motor/0/on/")) {
        int speed = msg.substring(strlen("motor/0/on/")).toInt();
        motor_on(0, speed);
    }
}

void onEvent(AsyncWebSocket *server, AsyncWebSocketClient *client, 
             AwsEventType type, void *arg, uint8_t *data, size_t len) {
    if (type == WS_EVT_CONNECT) {
        Serial.printf("Client connected: %u\n", client->id());
    } else if (type == WS_EVT_DISCONNECT) {
        Serial.printf("Client disconnected: %u\n", client->id());
        // Stop motors or mark GUI lost connection here
        motor_off(0);
        motor_off(1);
    } else if (type == WS_EVT_DATA) {
        handleWebSocketMessage(arg, data, len);
    }
}

void setup() {
    Serial.begin(115200);
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) delay(500);
    Serial.println(WiFi.localIP());

    ws.onEvent(onEvent);
    server.addHandler(&ws);
    server.begin();
}

void loop() {
    // Nothing needed here; AsyncWebServer handles everything
}


... more ... 

#include <WiFi.h>

const char* ssid = "Threat Level Midnight";
const char* password = "cowabunga2!!";

// Static IP settings
IPAddress local_IP(192,168,0,50);  // The IP you want
IPAddress gateway(192,168,0,1);   // Usually your router
IPAddress subnet(255,255,255,0);
IPAddress dns(8,8,8,8);           // Optional

void setup() {
    Serial.begin(115200);

    // Configure static IP
    if (!WiFi.config(local_IP, gateway, subnet, dns)) {
        Serial.println("STA Failed to configure");
    }

    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println();
    Serial.print("Connected. IP address: ");
    Serial.println(WiFi.localIP());
}

void loop() {
    // your code here
}


*/
