// TIRT_NATIVE_ADAPTER: handwritten Arduino adapter, independent of CAGEBOT.
#include <Arduino.h>
#include "controller.h"
#ifndef TIRT_LED_ENABLED
#define TIRT_LED_ENABLED 1
#endif
#ifndef TIRT_DEBUG_SERIAL
#define TIRT_DEBUG_SERIAL 0
#endif
#if TIRT_LED_ENABLED
#include <Adafruit_NeoPixel.h>
Adafruit_NeoPixel pixels(2, 13, NEO_GRB + NEO_KHZ800);
#endif
tirt::Controller controller;
uint8_t ledStatus = 0;
uint32_t telemetryAt = 0;

void statusLed(bool blue) {
    const uint8_t next = blue ? 2 : 1;
    if (next == ledStatus) return;
#if TIRT_LED_ENABLED
    pixels.setPixelColor(0, blue ? pixels.Color(0, 0, 255) : pixels.Color(51, 255, 51));
    pixels.show();
#endif
    ledStatus = next;
}

void writeWheels(tirt::Wheels wheels) {
    digitalWrite(7, wheels.left < 0 ? HIGH : LOW);
    analogWrite(5, wheels.left < 0 ? -wheels.left : wheels.left);
    digitalWrite(4, wheels.right < 0 ? LOW : HIGH);
    analogWrite(6, wheels.right < 0 ? -wheels.right : wheels.right);
}

void setup() {
    pinMode(12, INPUT);
    const uint8_t outputs[] = {7, 5, 4, 6};
    for (uint8_t pin : outputs) pinMode(pin, OUTPUT);
    for (uint8_t pin = A1; pin <= A5; ++pin) pinMode(pin, INPUT);
    writeWheels({0, 0});
#if TIRT_DEBUG_SERIAL
    Serial.begin(115200);
#endif
#if TIRT_LED_ENABLED
    pixels.begin(); pixels.show();
#endif
    controller.reset(); telemetryAt = 0; ledStatus = 0;
    statusLed(true);
    while (digitalRead(12) == HIGH) delay(20);
    statusLed(false);
}

void loop() {
    // Preserve baseline ADC read order; the core receives physical left-to-right.
    uint16_t adc[5];
    for (uint8_t i = 0; i < 5; ++i) adc[4-i] = analogRead(A1+i);
    const uint32_t now = millis();
    writeWheels(controller.tick(now, adc));
    statusLed(controller.blue());
#if TIRT_DEBUG_SERIAL
    if (uint32_t(now - telemetryAt) >= 50) {
        telemetryAt = now;
        for (uint8_t i = 0; i < 5; ++i) {
            Serial.print(F("A")); Serial.print(uint8_t(i+1)); Serial.print('='); Serial.print(adc[4-i]);
        }
        Serial.print(F("F=")); Serial.println(controller.state().f);
    }
#endif
}
