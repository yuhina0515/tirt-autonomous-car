#pragma once
#include "../layered_arduino/Arduino.h"
#include <stddef.h>
#include <vector>
uint32_t micros();
#define SERIAL_TX_BUFFER_SIZE 64
struct MockSerial {
 int capacity=63;unsigned long baud=0;int writes=0;
 std::vector<uint8_t> bytes;
 void begin(unsigned long value){baud=value;}
 int availableForWrite(){return capacity;}
 size_t write(const uint8_t* data,size_t size){writes++;bytes.insert(bytes.end(),data,data+size);return size;}
};
extern MockSerial Serial;
