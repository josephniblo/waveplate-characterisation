import os
import pyvisa
import pandas as pd
import matplotlib.pyplot as plt


# Known power meter IDs
PM100D_P0010673 = "USB0::4883::32888::P0010673::0::INSTR"

# Choose the power meter to connect to
METER_ID = PM100D_P0010673

LASER_WAVELENGTH = 1550  # nm


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

        # Connect to the power meter, make it beep and ask it for its ID
        print("Connecting to PM100D...")
        meter = rm.open_resource(res_found[0])
        meter.read_termination = "\n"
        meter.write_termination = "\n"
        meter.timeout = 3000  # ms

        meter.write("system:beeper")

        print("*idn?")
        print("--> " + meter.query("*idn?"))

        meter.write(f"SENS:CORR:WAV {LASER_WAVELENGTH}")  # wavelength
        meter.write("SENS:POW:UNIT W")  # watts
        meter.write("SENS:AVER:1000")

        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        run_calibration("waveplate", meter, timestamp)
        plot_calibration("waveplate", timestamp)

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


def run_calibration(
    waveplate_name: str, meter: pyvisa.resources.Resource, timestamp: str
):
    for w in range(360):
        rotate_waveplate_to(w)
        power = measure_power(meter)
        save_calibration_point(waveplate_name, w, power, timestamp)
    return


def rotate_waveplate_to(target_angle: int):
    # TODO: rotate waveplate
    print(f"Rotating waveplate to {target_angle} degrees")

    return


def measure_power(meter: pyvisa.resources.Resource):
    meter.write("MEAS:POW?")
    return meter.read()


def save_calibration_point(
    waveplate_name: str, angle: int, power: float, timestamp: str
):
    # Create the directory if it doesn't exist
    os.makedirs(
        f"calibration_data/{waveplate_name}/{timestamp}", exist_ok=True
    )

    file_path = (
        get_calibration_directory(waveplate_name, timestamp) + "/calibration.csv"
    )

    # Check if the file exists
    if os.path.exists(file_path):
        # If it exists, append the new data
        df = pd.read_csv(file_path)
        new_data = pd.DataFrame({"angle": [angle], "power": [power]})
        df = pd.concat([df, new_data], ignore_index=True)
    else:
        # If it doesn't exist, create a new DataFrame
        df = pd.DataFrame({"angle": [angle], "power": [power]})

    # Save the DataFrame to a CSV file
    df.to_csv(file_path, index=False)
    return


def plot_calibration(waveplate_name: str, timestamp: str):
    # Define the file path
    calibration_directory = get_calibration_directory(waveplate_name, timestamp)
    file_path = calibration_directory + "/calibration.csv"

    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Cannot plot: No calibration data found for {waveplate_name}")
        return

    # Read the calibration data
    df = pd.read_csv(file_path)

    # Plot the calibration data and save to a file
    plt.figure()
    plt.plot(df["angle"], df["power"], marker="o")
    plt.title(f"Calibration Data for {waveplate_name}")
    plt.xlabel("Angle (degrees)")
    plt.ylabel("Power (W)")
    plt.grid(True)
    plt.savefig(calibration_directory + "/calibration_plot.png")


def get_calibration_directory(waveplate_name: str, timestamp: str):
    return f"calibration_data/{waveplate_name}/{timestamp}"


if __name__ == "__main__":
    main()
