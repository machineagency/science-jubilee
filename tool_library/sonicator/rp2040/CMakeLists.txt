cmake_minimum_required(VERSION 3.13)

set(PICO_SDK_PATH $ENV{PICO_SDK_PATH})
include(~/Desktop/pico/pico-sdk/external/pico_sdk_import.cmake)

project(sonicator) # Replace `sonicator` with the name you want to give your project

pico_sdk_init()

add_executable(sonicator
    main.c  # Replace with the actual name of your C file
)

pico_enable_stdio_usb(sonicator 1)
pico_enable_stdio_uart(sonicator 0)

target_link_libraries(sonicator
    pico_stdlib
    hardware_i2c
)


pico_add_extra_outputs(sonicator)
