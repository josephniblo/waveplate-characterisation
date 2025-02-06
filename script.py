import pyvisa

# Known power meter IDs
PM100D_P0010673 = "USB0::4883::32888::P0010673::0::INSTR"

# Choose the power meter to connect to
METER_ID = PM100D_P0010673


def main():
    rm = None
    device = None

    try:
        rm = pyvisa.ResourceManager("@py")
        res_found = rm.list_resources(METER_ID)

        if len(res_found) == 0:
            print("No power meter found")
            raise Exception(
                "No power meter found. Check you are not connected in another program, eg. Thorlabs Optical Power Meter software."
            )

        # Connect to the power meter, make it beep, and ask it for its ID
        print("Connecting to PM100D...")
        meter = rm.open_resource(res_found[0])
        meter.read_termination = "\n"
        meter.write_termination = "\n"
        meter.timeout = 3000  # ms

        meter.write("system:beeper")

        print("*idn?")
        print("--> " + meter.query("*idn?"))

        # set wavelength setting, so the correct calibration point is used
        meter.write("SENS:CORR:WAV 1550")
        # set units to Watts
        meter.write("SENS:POW:UNIT W")
        # set averaging to 1000 points
        meter.write("SENS:AVER:1000")

        # read the power
        print(meter.query("MEAS:POW?"))

    except Exception as e:
        print("Error: " + str(e))
    finally:
        # Close device in any case
        if device is not None:
            try:
                device.close()
            except Exception:
                pass

        # Close resource manager in any case
        if rm is not None:
            try:
                meter.close()
            except Exception:
                pass
            # close out session
            rm.close()


if __name__ == "__main__":
    main()
