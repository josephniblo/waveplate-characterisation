# README

## Requirements

- Power meter
    - Install the ThorLabs software required to read the power meter
    - As of 2025-02-05, this is found at https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=OPM
    - Version 6.1
- libusb
    - C library to give generic access to USB devices
    - Download from https://libusb.info/
    - Version 1.0.27
- Python dependencies
    - Use [pipenv](https://pipenv.pypa.io/en/latest/) to install python dependencies
- Copy the libusb-1.0.dll into .venv/Scripts to make it available  
- NI-VISA
    - Used by PyUSB
    - Version 2025 Q1