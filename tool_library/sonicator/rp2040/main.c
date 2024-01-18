#include "pico/stdlib.h"
#include <stdio.h> 
#include "hardware/i2c.h"
#include <string.h>
#include "pico/binary_info.h"

// Define constant variables on board
const uint SONICATOR_PIN = 10;   // Replace with the GPIO pin number for the sonicator
const uint I2C_SDA_PIN = 26;
const uint I2C_SCL_PIN = 27;
const uint MAX_MESSAGE_LENGTH = 64;
i2c_inst_t* i2c_type= i2c1 ; // GPIO pins 26 & 27 are I2C 1 type
int I2C_DELAY = 5000 ;
int MCP4725_ADDR = 0x62; // Standard MCP4725 address when A0 connected to GND


void initialize_pins() {
    // Definies and initializes the sonicator GPIO pin
    gpio_init(SONICATOR_PIN);
    gpio_set_dir(SONICATOR_PIN, GPIO_OUT);
    gpio_put(SONICATOR_PIN, 0);
}

void initialize_i2c() {
    // Initializes the MCP4725 DAC I2C pins
        
    gpio_set_function(I2C_SDA_PIN, GPIO_FUNC_I2C);
    gpio_set_function(I2C_SCL_PIN, GPIO_FUNC_I2C);
    gpio_pull_up(I2C_SCL_PIN);
    gpio_pull_up(I2C_SDA_PIN);
    i2c_init(i2c1, 100000);  // Initialize I2C with a baud rate of 100,000
    busy_wait_ms(50);
}

void set_dac_value(float value) {
    // Convert the DAC value to a 12-bit integer (0-4095)
    uint16_t dac_value = (uint16_t)(value * 4095);

    // MCP4725 I2C write command
    uint8_t write_mode = 0x00; // fast write mode for MCP4725 DAC 
    // MCP4725 I2C write command
    uint8_t data[2] = {write_mode| (uint8_t)((dac_value >> 8)), (uint8_t)(dac_value & 0x00FF)};

    // Write data to MCP4725
    i2c_write_timeout_us(i2c_type, MCP4725_ADDR, data, sizeof(data), false, I2C_DELAY);
    
    printf("DAC value set to %f V\n",value*5);
    busy_wait_ms(50);
}

void turn_on_sonicator() {
    // Turn on sonicator (replace with your code)
    printf("Turning ON sonicator\n");
    gpio_put(SONICATOR_PIN, 1);
    busy_wait_ms(50);
}

void turn_off_sonicator() {
    // Turn off sonicator (replace with your code)
    printf("Turning OFF sonicator\n");
    gpio_put(SONICATOR_PIN, 0);
    busy_wait_ms(50);
}

void communication_init() {
    // Initialize usb communication with Pico
    stdio_usb_init();
    stdio_set_translate_crlf(&stdio_usb, false); // Do not translate \n to \r\n
    while (!stdio_usb_connected()) {} // Wait for USB CDC connection
}

void get_message(char* message) {
    // Get message from USB CDC
    size_t indx_ = 0;

    // Check if a character is available
    int new_char = getchar_timeout_us(0);
    while ( new_char != PICO_ERROR_TIMEOUT) {
        message[indx_++] = (char)new_char;
        new_char = getchar_timeout_us(0);
    }
    char last_char = message[indx_- 1];
    if (last_char == '\n' || last_char == '\r') {
        message[indx_] = '\0'; // Terminate the string
    }
}

int main() {
    
    stdio_init_all();
    
    // Initialize USB CDC communication
    communication_init();

    // Initialize GPIO pins
        
    initialize_pins();

    // Initialize I2C
    initialize_i2c();
    
    // Make pin information available for picotool
    bi_decl(bi_program_description("Interface for QSonica Sonicator Board"));
    bi_decl(bi_1pin_with_name(SONICATOR_PIN, "Sonicator ON/OFF Pin"));
    bi_decl(bi_1pin_with_name(I2C_SDA_PIN, "I2C SDA Pin"));
    bi_decl(bi_1pin_with_name(I2C_SCL_PIN, "I2C SCL Pin"));
        
    char message[MAX_MESSAGE_LENGTH];
    
    while (1) {
        // Handle USB CDC communication
        while (stdio_usb_connected()) {

            // Read command from USB CDC
            get_message(message);
            char* command = strtok(message, " \r\n");
            size_t read_bytes = strlen(command);

            // Process the received command
            if (read_bytes > 0) {

                // Process the command and perform actions
                if (strncmp(command, "DAC:", 4) == 0) {
                    // Process DAC command
                    strtok(command,":");
                    char* value_str = strtok(NULL,"");
                    float value;
                    sscanf(value_str,"%f", &value);
                    set_dac_value(value);
                } else if (strcmp(command, "SONICATOR_ON") == 0) {
                    // Process command to turn on sonicator
                    turn_on_sonicator();
                } else if (strcmp(command, "SONICATOR_OFF") == 0) {
                    // Process command to turn off sonicator
                    turn_off_sonicator();
                }
            }
        }
    }

    return 0;
}
