#include <WiFi.h>
#include <Arduino.h>

const int IN1 = 2;
const int IN2 = 4;
const int IN3 = 19;
const int IN4 = 18;

const char* ssid = "Threat Level Midnight";
const char* password = "cowabunga2!!";

// Pick an IP outside your router's DHCP range
IPAddress local_IP(192,168,0,50);  
IPAddress gateway(192,168,0,1);    
IPAddress subnet(255,255,255,0);   
IPAddress dns(8,8,8,8);      

WiFiServer server(80);

int ledPin = 2;  // built-in LED

void motor_on(int number){
  if (number){
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
  }
  else {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
  }
}

void motor_off(int number){
  if (number){
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
  }
  else {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, LOW);
  }
}

void setup() {
  Serial.begin(115200);

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
  client.flush();

  // Get Request
  if (req.indexOf("/motor/0/on") != -1)  motor_on(0);
  if (req.indexOf("/motor/1/on") != -1)  motor_on(1);
  
  if (req.indexOf("/motor/0/of") != -1)  motor_off(0);
  if (req.indexOf("/motor/1/of") != -1)  motor_off(1);

  // Reply
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: text/plain");
  client.println();
  client.print("LED: "); client.println(digitalRead(ledPin) ? "ON" : "OFF");

  client.stop();
}
