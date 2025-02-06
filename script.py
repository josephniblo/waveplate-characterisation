"""
PMxxx_SCPI
Example Date of Creation: 2023-10-09
Example Date of Last Modification on Github: 2023-10-09
Version of Python: 3.11
Version of the Thorlabs SDK used: -
==================
Example Description: The example shows how to use SCPI commands in Python with pyvisa
"""

#Import the PyVISA library to Python.
import pyvisa

def main():
    rm = None
    device = None

    #Opens a resource manager
    rm = pyvisa.ResourceManager('@py')
    # rm = pyvisa.ResourceManager()

    res_found = rm.list_resources('USB0::4883::32888::P0010673::0::INSTR')
    # res_found = rm.list_resources('ASRL3::INSTR')

    #Opens the connection to the device. The variable instr is the handle for the device.
    # !!! In the USB number the serial number (P00...) and PID (0x8078) needs to be changed to the one of the connected device.
    #Check with the Windows DEvice Manager
   
    # Connect to the power meter, make it beep, and ask it for its ID
    print('Connecting to PM100D...')
    meter = rm.open_resource(res_found[0])
    meter.read_termination = '\n'
    meter.write_termination = '\n'
    meter.timeout = 3000  # ms

    meter.write('system:beeper')

    print('*idn?')
    print('--> ' + meter.query('*idn?'))
    
    # #print the device information
    # print(instr.query("SYST:SENS:IDN?"))
    
    # #turn on auto-ranging
    # instr.write("SENS:RANGE:AUTO ON")
    #set wavelength setting, so the correct calibration point is used
    meter.write("SENS:CORR:WAV 1310")
    #set units to Watts
    meter.write("SENS:POW:UNIT W")
    #set averaging to 1000 points
    meter.write("SENS:AVER:1000")

    #read the power
    print (meter.query("MEAS:POW?"))

    #Close device in any case
    if device is not None:
        try:
            device.close()
        except Exception:
            pass

    #Close resource manager in any case
    if rm is not None:
        try:
            meter.close()
        except Exception:
            pass

    #close out session
    rm.close()

if __name__ == "__main__":
    main()