// TODO: Scan for available wifi instead of hard coding

#include <WiFi.h>
#include <Arduino.h>
#include <ESPAsyncWebServer.h>
#include <ESPmDNS.h>
#include <driver/i2s.h>

// WiFi credentials
const char* ssid = "Threat Level Midnight";
const char* password = "cowabunga2!!";
// const char* ssid = "BYUI_Visitor";
// const char* password = "";

// WebSocket server
AsyncWebServer server(81);
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
uint32_t activeClientId = 0;

// I2S pins
#define I2S_WS 14
#define I2S_SCK 33
#define I2S_SD 32

// I2S configuration
#define I2S_SAMPLE_RATE 16000
#define I2S_BUFFER_SIZE 1024

AsyncWebSocket audio_ws("/audio");  // new endpoint
uint32_t activeAudioClient = 0;

void onAudioWS(AsyncWebSocket *server, AsyncWebSocketClient *client, AwsEventType type,
               void *arg, uint8_t *data, size_t len) {
    if(type == WS_EVT_CONNECT) {
        if(activeAudioClient != 0) client->close(); // only 1 audio client
        activeAudioClient = client->id();
        Serial.printf("Audio client connected: %u\n", activeAudioClient);
    } else if(type == WS_EVT_DISCONNECT) {
        if(client->id() == activeAudioClient) activeAudioClient = 0;
        Serial.println("Audio client disconnected");
    }
}

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

        if (activeClientId != 0){
            Serial.printf("Rejecting client %u, already connected to client %u\n"),
                client->id(), activeClientId;
                client->close();
                return;
        }
        activeClientId = client->id();
        Serial.printf("Client connected: %u\n", activeClientId);
    }

    else if (type == WS_EVT_DISCONNECT) {
        Serial.printf("Client disconnected: %u\n", client->id());
        if (ws.count() == 0) {
            Serial.println("No clients connected");
            activeClientId = 0;
            motor_off(0);
            motor_off(1);
        }
    }

    else if (type == WS_EVT_DATA) { // data received
        AwsFrameInfo *info = (AwsFrameInfo*)arg;
        if(info->final && info->len == 5 && info->opcode == WS_BINARY) {

            if (client->id() != activeClientId) return;

            byte opcode       = data[0];
            byte motor_number = data[1];
            byte power        = data[2];
            byte pwm          = data[3];
            byte direction    = data[4];

            Serial.print("Opcode: "); Serial.print(opcode);
            Serial.print(" Motor: "); Serial.print(motor_number);
            Serial.print(" Power: "); Serial.print(power);
            Serial.print(" PWM: "); Serial.print(pwm);
            Serial.print(" Direction: "); Serial.print(direction); Serial.print("\n");

            if(!opcode){ // Motor opcode = 0000
                if (power) motor_on(motor_number, pwm, direction);
                else motor_off(motor_number);
            }
        }
    }
    
    else if (type == WS_EVT_PONG) {
        // Client responded to our ping - connection is alive
        Serial.printf("Pong received from client %u\n", client->id()); 
    }
}

void setup() {
  Serial.begin(921600);

  ledcSetup(channelA, freq, resolution);
  ledcAttachPin(enableA, channelA);

  ledcSetup(channelB, freq, resolution);
  ledcAttachPin(enableB, channelB);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.print(".");
  }

  // Start mDNS for friendly hostname
  if (MDNS.begin("stc_esp")) {
      Serial.println("mDNS started: stc_esp.local");
  }

  Serial.println();
  Serial.print("ESP IP: ");
  Serial.println(WiFi.localIP());

  ws.onEvent(onWebSocketEvent);
  server.addHandler(&ws);
  audio_ws.onEvent(onAudioWS);
  server.addHandler(&audio_ws);
  server.begin();

  // Configure I2S
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = I2S_SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    // .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .communication_format = I2S_COMM_FORMAT_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = I2S_BUFFER_SIZE,
    .use_apll = false
  };

  // Install I2S driver  (FIXED: I2S_NUM_0)
  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);

  // Set I2S pins
  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = -1,
    .data_in_num = I2S_SD
  };

  i2s_set_pin(I2S_NUM_0, &pin_config);
}

void loop() {
  // Send ping to all connected clients every 1 second
  if (millis() - lastPingTime > PING_INTERVAL) {
      lastPingTime = millis();
      ws.pingAll();  // Send ping to detect dead connections
      ws.cleanupClients();
  }   
  



  int32_t audio_samples[I2S_BUFFER_SIZE];
  size_t bytes_read;

  i2s_read(I2S_NUM_0, audio_samples, sizeof(audio_samples), &bytes_read, portMAX_DELAY);

  // Serial.write((uint8_t*)audio_samples, bytes_read);
  // ws.binary(activeClientId, (uint8_t*)audio_samples, bytes_read);
  // if (activeClientId != 0) {
  //   ws.binary(activeClientId, (uint8_t*)audio_samples, bytes_read);
  // }
  if(activeAudioClient != 0) {
      audio_ws.binary(activeAudioClient, (uint8_t*)audio_samples, bytes_read);
  }
}




