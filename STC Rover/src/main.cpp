#include <WiFi.h>

const char* ssid = "Threat Level Midnight";
const char* password = "cowabunga2!!";

void setup() {
  Serial.begin(115200);

  WiFi.mode(WIFI_STA); // Wifi Station
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("Connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
}
