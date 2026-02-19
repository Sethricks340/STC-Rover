#include <driver/i2s.h>
#include <Arduino.h>
#include <math.h>

#define SAMPLE_RATE 22050
#define TONE_FREQ   440    // A4
#define PI 3.14159265

// I2S config
i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_RIGHT,
    .communication_format = I2S_COMM_FORMAT_I2S_MSB,
    .intr_alloc_flags = 0,
    .dma_buf_count = 4,
    .dma_buf_len = 1024,
    .use_apll = false,
    .tx_desc_auto_clear = true,
    .fixed_mclk = 0
};

i2s_pin_config_t pin_config = {
    .bck_io_num = 21,
    .ws_io_num = 19,
    .data_out_num = 22,
    .data_in_num = I2S_PIN_NO_CHANGE
};

// phase accumulator
float phase = 0;
float phaseIncrement = 2 * PI * TONE_FREQ / SAMPLE_RATE;

void setup() {
    Serial.begin(115200);
    i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
    i2s_set_pin(I2S_NUM_0, &pin_config);
    Serial.println("I2S initialized");
}

void loop() {
    const int bufSize = 512;
    int16_t buffer[bufSize];

    // fill buffer with sine wave
    for (int i = 0; i < bufSize; i++) {
        buffer[i] = 12000 * sin(phase); // larger amplitude for audible output
        phase += phaseIncrement;
        if (phase > 2 * PI) phase -= 2 * PI;
    }

    size_t bytesWritten;
    i2s_write(I2S_NUM_0, buffer, bufSize * sizeof(int16_t), &bytesWritten, portMAX_DELAY);
}