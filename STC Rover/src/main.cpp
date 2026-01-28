#include <WiFi.h>
#include <Arduino.h>

const int IN3 = 19; // IN3
const int IN4 = 18; // IN4

const char* ssid = "Threat Level Midnight";
const char* password = "cowabunga2!!";

// Pick an IP outside your router's DHCP range
IPAddress local_IP(192,168,0,50);  
IPAddress gateway(192,168,0,1);    
IPAddress subnet(255,255,255,0);   
IPAddress dns(8,8,8,8);      

WiFiServer server(80);

int ledPin = 2;  // built-in LED

void motor_on(){
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
}

void motor_off(){
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, LOW);
}

void setup() {
  Serial.begin(115200);

  pinMode(ledPin, OUTPUT);
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

  // // Control LED
  // if (req.indexOf("/on") != -1)  digitalWrite(ledPin, HIGH);
  // if (req.indexOf("/off") != -1) digitalWrite(ledPin, LOW);

  // Control LED
  if (req.indexOf("/on") != -1)  motor_on();
  if (req.indexOf("/off") != -1) motor_off();

  // Reply
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: text/plain");
  client.println();
  client.print("LED: "); client.println(digitalRead(ledPin) ? "ON" : "OFF");

  client.stop();
}
