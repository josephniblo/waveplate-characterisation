import os
import warnings
import pyvisa
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit


# Known power meter IDs
PM100D_P0010673 = "USB0::4883::32888::P0010673::0::INSTR"
PM100D_P0028831 = "USB0::4883::32888::P0028831::0::INSTR"

# Choose the power meter to connect to
METER_ID = PM100D_P0028831

LASER_WAVELENGTH = 1550  # nm


# enum for waveplate type
class WaveplateType:
    HWP = 0
    QWP = 1


def main():
    rm = None
    device = None

    try:
        rm = pyvisa.ResourceManager("@py")

        # Suppress needless warnings
        warnings.filterwarnings(
            "ignore",
            message="TCPIP::hislip resource discovery requires the zeroconf package",
        )
        warnings.filterwarnings(
            "ignore",
            message="TCPIP:instr resource discovery is limited to the default interface.Install psutil",
        )

        res_found = rm.list_resources(METER_ID)

        if len(res_found) == 0:
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

        # Get the name of the waveplate
        waveplate_name = input("Enter the name of the waveplate: ")

        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        print("Calibration timestamp: " + timestamp)

        run_calibration(waveplate_name, meter, timestamp)
        plot_calibration(waveplate_name, timestamp)
        print(fit_calibration(waveplate_name, timestamp))

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
    os.makedirs(f"calibration_data/{waveplate_name}/{timestamp}", exist_ok=True)

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


def fit_calibration(waveplate_name: str, timestamp: str):
    calibration_directory = get_calibration_directory(waveplate_name, timestamp)
    file_path = calibration_directory + "/calibration.csv"

    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Cannot plot: No calibration data found for {waveplate_name}")
        return

    # Read the calibration data
    df = pd.read_csv(file_path)

    # Fit a HWP sinusoid to the calibration data
    # HWP has period pi
    def hwp_sinusoid(theta, offset, amplitude, phase):
        return offset + amplitude * np.sin(2 * 2 * np.pi * (theta - phase) / 360)

    # QWP has period pi/2
    def qwp_sinusoid(theta, offset, amplitude, phase):
        return offset + amplitude * np.sin(4 * 2 * np.pi * (theta - phase) / 360)

    # Fit the HWP & QWP sinusoid to the calibration data
    popt_hwp, pcov_hwp = curve_fit(hwp_sinusoid, df["angle"], df["power"], p0=[1, 1, 0])
    popt_qwp, pcov_qwp = curve_fit(qwp_sinusoid, df["angle"], df["power"], p0=[1, 1, 0])

    # determine which is the better fit
    hwp_residuals = df["power"] - hwp_sinusoid(df["angle"], *popt_hwp)
    qwp_residuals = df["power"] - qwp_sinusoid(df["angle"], *popt_qwp)
    hwp_residuals = np.sum(hwp_residuals**2)
    qwp_residuals = np.sum(qwp_residuals**2)

    waveplate_type = None
    fit_offset = None
    if hwp_residuals < qwp_residuals:
        waveplate_type = WaveplateType.HWP
        fit_offset = popt_hwp[0]
        fit_amplitude = popt_hwp[1]
        fit_phase = popt_hwp[2]
        print("Determined to be HWP")
    else:
        waveplate_type = WaveplateType.QWP
        fit_offset = popt_qwp[0]
        fit_amplitude = popt_qwp[1]
        fit_phase = popt_qwp[2]
        print("Determined to be QWP")

    # Plot the calibration data and the fitted sinusoid
    plt.figure()
    plt.plot(df["angle"], df["power"], marker="o", label="Calibration Data")
    if waveplate_type == WaveplateType.HWP:
        plt.plot(df["angle"], hwp_sinusoid(df["angle"], *popt_hwp), label="HWP Fit")
    else:
        plt.plot(df["angle"], qwp_sinusoid(df["angle"], *popt_qwp), label="QWP Fit")

    plt.title(f"Calibration Data for {waveplate_name}")
    plt.xlabel("Angle (degrees)")
    plt.ylabel("Power (W)")
    plt.grid(True)
    plt.legend()
    plt.text(
        0.95,
        0.95,
        f"Offset: {fit_offset:.2f}\nAmplitude: {fit_amplitude:.2f}\nPhase: {fit_phase:.2f}",
        horizontalalignment="right",
        verticalalignment="top",
        transform=plt.gca().transAxes,
    )

    plt.savefig(calibration_directory + "/calibration_fit.png")

    with open(calibration_directory + "/calibration_fit.json", "w") as f:
        f.write(
            f'{{"waveplate_type": {waveplate_type}, "fit_offset": {fit_offset:.2e}, "fit_amplitude": {fit_amplitude:.2e}, "fit_phase": {fit_phase:.2e}}}'
        )

    return waveplate_type, fit_offset, fit_amplitude, fit_phase


def get_calibration_directory(waveplate_name: str, timestamp: str):
    return f"calibration_data/{waveplate_name}/{timestamp}"


if __name__ == "__main__":
    main()
