import matplotlib.pyplot as plt
import numpy as np

import coilgun_sim as cgsim
import coilgun_utils as cgutil

# Constants
# Flyback diode and it's series resistor parameters
RF = 4.7            # Ohms (Resistance of the flyback diode)
VF = 0.7            # Volts (Forward voltage drop of the flyback diode)
DIODE = True        # If we have a flyback diode or not

# TODO: Constant current instead of capacitor
# TODO: FET/IGBT-based switching
# TODO: FET/IGBT-based half-bridge switching with energy recovery

STEP_TIME = 0.1e-5  # Step time (s)
SIM_TIME = 5e-3   # Total simulation time (s)

def draw(time, results):
    # Plot the results
    _, ax1 = plt.subplots()

    ax1.grid(axis='x', color='0.95')
    ax1.grid(axis='y', color='0.95')

    # Left side plot
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Capacitor Voltage (V)', color='tab:blue')
    ax1.plot(time, results[:, 1], label='Capacitor Voltage', color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    # Right side plot
    ax = ax1.twinx()
    ax.set_ylabel('Coil Current (A)', color='tab:orange')
    ax.plot(time, results[:, 0], label='Current', color='tab:orange')
    ax.tick_params(axis='y', labelcolor='tab:orange')

    # Right side plot
    ax = ax1.twinx()
    ax.set_ylabel('Velocity (m/s)', color='tab:red')
    ax.plot(time, results[:, 2], label='Velocity', color='tab:red')
    ax.tick_params(axis='y', labelcolor='tab:red')

    plt.title("CoilGun Simulator")
    plt.show()

def main():
    # Time array
    time = np.arange(0, SIM_TIME, STEP_TIME)

    # Main parameters
    C = 680e-6          # Farads
    ESR = 0.34          # Ohms
    V0 = 440            # Volts

    D0 = 20             # Projectile starting distance
    VP0 = 0             # Projectile starting speed

    # Projectile parameters
    PL = 25
    PD = 8

    # Coil parameters
    CW = 0.9            # Coil wire size
    CL = 20             # Coil length
    CT = 170            # Coil turns

    # Load coil data
    data, desc = cgutil.load_cgdata('%.1f_C%dx%dT-P%.1fx%d' % (CW, CL, CT, PD, PL))

    # Setup and simulate
    cgsim.setup(0, data, desc, C, ESR, VF, RF, DIODE, [0, V0, VP0, D0, 0])
    results = cgsim.simulate(time, STEP_TIME) # i(0) = 0 A, V_c(0) = V0 V, v=0m/s, d=distance, W=0J

    # Get peak currents, voltages and get final velocity
    peak_current_max = np.max(results[:, 0])
    peak_voltage_max = np.max(results[:, 1])
    peak_current_min = np.min(results[:, 0])
    peak_voltage_min = np.min(results[:, 1])
    final_velocity = results[len(results) - 1, 2]
    final_energy = results[len(results)-1, 4]

    print("Peak Current: %.2f/%.2f A" % (peak_current_min, peak_current_max))
    print("Peak Voltage: %.2f/%.2f V" % (peak_voltage_min, peak_voltage_max))
    print("Final Velocity: %.2f m/s" % final_velocity)
    print("Muzzle energy = %.2fJ" % (final_energy))

    draw(time, results)

def main_sweep():
    # Time array
    time = np.arange(0, SIM_TIME, STEP_TIME)

    # Main parameters
    C = 330e-6         # Farads
    ESR = 0.4          # Ohms
    V0 = 440           # Volts

    VP0 = 54           # Projectile starting speed

    # Projectile parameters
    PL = 20
    PD = 8

    CW = 0.9
    
    # Coil length
    CLR = [ 30]

    # Coil turns
    CTR = [ 150, 300 ]
    CTS = 10 # 10 turns step
    CTN = int((CTR[1] - CTR[0]) / CTS)

    DS = 10
    DR = 30

    FD = 3.5 # Fixed starting distance

    max_velocity = 0
    best_parameters = {}

    #for i in range(0, DR+1):
    for j in range(0, len(CLR)):
        for k in range(0, CTN):
            #D = DS + i
            CL = CLR[j]
            CT = CTR[0] + k * CTS

            D = CL / 2 + PL / 2 + FD

            # Load coil data
            data, desc = cgutil.load_cgdata('%.1f_C%dx%dT-P%.1fx%d' % (CW, CL, CT, PD, PL))

            # Setup and simulate
            cgsim.setup(0, data, desc, C, ESR, VF, RF, DIODE, [0, V0, VP0, D, 0])
            results = cgsim.simulate(time, STEP_TIME) # i(0) = 0 A, V_c(0) = V0 V, v=0m/s, d=distance, W=0J
            velocity = results[len(results) - 1, 2]

            if velocity > max_velocity:
                max_velocity = velocity
                dist = D - (PL/2 + CL/2)
                current = results[len(results) - 1, 0]
                leftover_voltage = results[len(results) - 1, 1]
                best_parameters = {'dist': dist, 'cdist' : D, 'CL': CL, 'CT': CT}

    print('\nHighest Velocity: %.1f (dV=%.1f) m/s @ %.1fA left: %.1fV' % (max_velocity, max_velocity - VP0, current, leftover_voltage))
    print(f"Best Parameters: {best_parameters}")
    pass

if __name__ == "__main__":
    #main() # Simulates a single coil
    main_sweep() # Looks for best coil design for a given projectile, coil, capacitor etc.
    # TODO: Implement a sweep for the whole coilgun design