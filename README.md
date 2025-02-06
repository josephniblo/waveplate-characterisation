# README

This script connects to a PM100D Thor Labs Power meter.

## Requirements

- Python dependencies
    - Use [pipenv](https://pipenv.pypa.io/en/latest/) to install python dependencies
- Copy the libusb-1.0.dll into .venv/Scripts to make it available to the script

## Gotchas

- Only one thing can connect to the device at a time - if you are connected in eg. Optical Power Monitor software, it will not show up to the python script.

## Alternative

- Install the ThorLabs software required to read the power meter
- As of 2025-02-05, this is found at https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=OPM, version 6.1
- This has a nice GUI for interacting with the Power Meter