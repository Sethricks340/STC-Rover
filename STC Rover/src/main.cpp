// TODO: Make so only one client at a time can connect
// Change Static IP so it works on any network, on GUI as well

#include <WiFi.h>
#include <Arduino.h>
#include <ESPAsyncWebServer.h>

// WiFi credentials
const char* ssid = "Threat Level Midnight";
const char* password = "cowabunga2!!";

// Static IP config
IPAddress local_IP(192,168,0,50);
IPAddress gateway(192,168,0,1);
IPAddress subnet(255,255,255,0);
IPAddress dns(8,8,8,8);

// WebSocket server
AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

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

unsigned long lastPingTime = 0;
const unsigned long PING_INTERVAL = 500; // Send ping at 2 Hz

void motor_on(int number, int pwm, int direction) {
    int inA, inB, channel;

    if (number) { // Motor 1
        inA = IN3;
        inB = IN4;
        channel = channelB;
    } else {      // Motor 0
        inA = IN1;
        inB = IN2;
        channel = channelA;
    }

    digitalWrite(inA, direction ? LOW : HIGH);
    digitalWrite(inB, direction ? HIGH : LOW);
    ledcWrite(channel, pwm);
}

void motor_off(int number) {
    int inA, inB, channel;

    if (number) {
        inA = IN3;
        inB = IN4;
        channel = channelB;
    } else {
        inA = IN1;
        inB = IN2;
        channel = channelA;
    }

    digitalWrite(inA, LOW);
    digitalWrite(inB, LOW);
    ledcWrite(channel, 0);
}

// WebSocket event handler
void onWebSocketEvent(
    AsyncWebSocket *server,
    AsyncWebSocketClient *client,
    AwsEventType type,
    void *arg,
    uint8_t *data,
    size_t len
) {
    if (type == WS_EVT_CONNECT) {
        Serial.printf("Client connected: %u\n", client->id());
    }
    else if (type == WS_EVT_DISCONNECT) {
        Serial.printf("Client disconnected: %u\n", client->id());
        if (ws.count() == 0) {
            Serial.println("No clients connected");
            motor_off(0);
            motor_off(1);
        }
    }

    else if (type == WS_EVT_DATA) { // data received
        AwsFrameInfo *info = (AwsFrameInfo*)arg;
        if(info->final && info->len == 5 && info->opcode == WS_BINARY) {
            byte opcode       = data[0];
            byte motor_number = data[1];
            byte power        = data[2];
            byte pwm          = data[3];
            byte direction    = data[4];

            Serial.print("Opcode: "); Serial.println(opcode);
            Serial.print("Motor: "); Serial.println(motor_number);
            Serial.print("Power: "); Serial.println(power);
            Serial.print("PWM: "); Serial.println(pwm);
            Serial.print("Direction: "); Serial.println(direction); Serial.println("\n");

            if(!opcode){ // Motor opcode = 0000
                if (power){
                    motor_on(motor_number, pwm, direction);
                }
                else{
                    motor_off(motor_number);
                }
            }
        }
    }
    
    else if (type == WS_EVT_PONG) {
        // Client responded to our ping - connection is alive
        Serial.printf("Pong received from client %u\n", client->id()); 
    }
}

void setup() {
    Serial.begin(115200);

    ledcSetup(channelA, freq, resolution);
    ledcAttachPin(enableA, channelA);

    ledcSetup(channelB, freq, resolution);
    ledcAttachPin(enableB, channelB);

    pinMode(IN1, OUTPUT);
    pinMode(IN2, OUTPUT);
    pinMode(IN3, OUTPUT);
    pinMode(IN4, OUTPUT);

    if (!WiFi.config(local_IP, gateway, subnet, dns)) {
        Serial.println("Static IP config failed");
    }

    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println();
    Serial.print("ESP IP: ");
    Serial.println(WiFi.localIP());

    ws.onEvent(onWebSocketEvent);
    server.addHandler(&ws);
    server.begin();
}

void loop() {
    // Send ping to all connected clients every 1 second
    if (millis() - lastPingTime > PING_INTERVAL) {
        lastPingTime = millis();
        ws.pingAll();  // Send ping to detect dead connections
        ws.cleanupClients();
    }    
}