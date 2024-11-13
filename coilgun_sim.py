import numpy as np
import coilgun_utils as cgutil
import math

freewheeling_diode = True

coil_resistance = 0

method = 0

capacitor_value = 0
capacitor_esr = 0
fdiode_voltage = 0
fdiode_resistance = 0
projectile_mass = 0
neg_didt = False

initial_conditions = []
data = []
desc = {}

def lerp(a, b, f):
    return a + f * (b - a)

# SCR-based
# This equation represents the rate of change of load current with respect to time.
# It includes an optional flyback diode.
def SCR_dIdt(cv, li, l):
    # cv - capacitor voltage
    # li - inductor current
    # l  - inductor inductance

    # Freewheeling diode simulation
    flyback_current = 0

    # Diode forward voltage threshold (typically ~0.7V for silicon diodes)
    diode_threshold_voltage = 0.7

    # Check if diode conducts (when current is negative or cv < -diode_threshold_voltage)
    if freewheeling_diode and (li < 0 or cv < -diode_threshold_voltage):
        # Apply the voltage drop across the diode when conducting
        cv -= diode_threshold_voltage
        # Flyback current kicks in only when the current is negative or the voltage is low enough
        flyback_current = li  # Diode conducts the current

    # Vc(t) - i(t) * (R + ESR) - L * di/dt
    # where:
    #   Vc(t) is the capacitor voltage,
    #   i(t) is the load current,
    #   R is the load resistor,
    #   ESR is the equivalent series resistance,
    #   L is the inductance,
    #   di/dt is the rate of change of current,
    return (cv - li * (coil_resistance + capacitor_esr) - flyback_current) / l

# SCR-based dVdt
# This equation represents the rate of change of capacitor voltage with respect to time.
def SCR_dVdt(cv, li):
    if freewheeling_diode and cv < -fdiode_voltage:
        return 0 # Capacitor's voltage does not change when the freewheeling diode takes action
    
    # i=C(dv/dt)
    # where:
    #   i is the load current,
    #   C is the capacitance.
    return -li / capacitor_value


# FET/IGBT-based dIdt
# This equation represents the rate of change of load current with respect to time.
def FET_dIdt(cv, li, l):
    # cv - current voltage
    # li - inductor current
    # l  - inductor inductance

    # TODO
    pass

# FET/IGBT-based dVdt
# This equation represents the rate of change of capacitor voltage with respect to time.
def FET_dVdt(cv, li):
    # TODO
    pass

# dIdt
# This equation represents the rate of change of load current with respect to time.
def HB_FET_dIdt(cv, li, l):
    # cv - current voltage
    # li - inductor current
    # l  - inductor inductance

    # TODO
    pass

# dVdt
# This equation represents the rate of change of capacitor voltage with respect to time.
def HB_FET_dVdt(cv, li):
    # TODO
    pass

# Euler method for solving differential equations
def dUdt(step, previous, dt):
    global neg_didt
    
    current, voltage, velocity, distance, workSum = previous
    
    if current < 0 and step != 0:
        return [current, voltage, velocity, distance, workSum]
    
    row = cgutil.get_data_interpolated(data, desc, current, distance)
    inductance = row[1] * 1e-6
    force = row[2]

    if method == 0:
        di_dt = SCR_dIdt(voltage, current, inductance)
        dv_dt = SCR_dVdt(voltage, current)
    elif method == 1:
        di_dt = FET_dIdt(voltage, current, inductance)
        dv_dt = FET_dVdt(voltage, current)
    elif method == 2:
        di_dt = HB_FET_dIdt(voltage, current, inductance)
        dv_dt = HB_FET_dVdt(voltage, current)
    else:
        raise ValueError("Invalid method")

    neg_didt = di_dt < 0

    current += dt * di_dt
    voltage += dt * dv_dt

    # Convert to milliseconds
    acceleration = force / projectile_mass
    
    # Calculate velocity
    velocity += acceleration * dt

    # Calculate the step (i.e. displacement over Z axis)
    displacement = velocity * dt * 1000

    # Add to the sum of the work
    workSum += (displacement / 1000) * force
    
    # Adjust the distance
    distance -= displacement

    #print("[%d] t=%.2fms d=%.2fmm v=%.2fm/s (a=%.2fm/s^2 i=%.3fA f=%.1fN) L=%.1fuH" % (step, t*1000, distance, velocity, acceleration, current, force, inductance / 1e-6))

    return [current, voltage, velocity, distance, workSum]

def calculate_coil_resistance(_desc):
    return 1.68e-8 * _desc['CoilData']['WireLength'] / (math.pi * ((_desc['CoilData']['WireDiameter'] * 0.5) / 1000.0) ** 2)

def setup(_method, _data, _desc, _capacitor_value, _capacitor_esr, _fdiode_voltage, _fdiode_resistance, _freewheeling_diode, _initial_conditions):
    global data, desc
    global capacitor_value, capacitor_esr, fdiode_voltage, fdiode_resistance, freewheeling_diode
    global coil_resistance, projectile_mass
    global initial_conditions
    global method

    method = _method

    data = _data
    desc = _desc

    capacitor_value = _capacitor_value
    capacitor_esr = _capacitor_esr
    fdiode_voltage = _fdiode_voltage
    fdiode_resistance = _fdiode_resistance
    freewheeling_diode = _freewheeling_diode

    initial_conditions = _initial_conditions

    coil_resistance = desc['CoilData']['Resistance'] ##calculate_coil_resistance(_desc)
    projectile_mass = desc['ProjectileData']['Mass'] / 1000

    pass

def simulate(time, step_time):

    # Simulation using Euler method
    results = np.zeros((len(time), 5))
    results[0, :] = initial_conditions

    for i in range(1, len(time)):
        results[i, :] = dUdt(i, results[i-1, :], step_time)

    return results
