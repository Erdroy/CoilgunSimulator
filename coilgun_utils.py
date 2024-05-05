import math
import json

def lerp(a, b, f):
    return a + f * (b - a)

def get_data_raw(data, index):
    return data[index]

def get_data_interpolated(data, desc, current, distance):
    # Sign affects if the projectile should be accelerated or decelerated (if the force should become positive or negative)
    sign = 1
    if distance < 0 or current < 0:
        sign = -1

    distance = abs(distance)
    current = abs(current)

    lower_index = math.floor(distance)
    upper_index = math.ceil(distance)

    if lower_index >= len(data) or upper_index >= len(data):
        return (
            distance * sign,
            data[len(data) - 1][1], # Inductance
            0 # Force TODO: Extrapolate force
        )

    distance_weigth = distance
    distance_weigth -= math.ceil(distance_weigth)

    currents = desc['Currents']
    #assert current <= currents[len(currents) - 1]

    data_a = data[lower_index]
    data_b = data[upper_index]

    # Deal with current interpolation
    # TODO: Improve these two if's (select two nearest forces, and extrapolate)
    if current < currents[0]:
        t = max(current / currents[0], 0)
        
        inductance = lerp(data_a[1], data_b[1], distance_weigth)
        force = lerp(0, data_b[2], t) * sign

        return (distance * sign, inductance, force)

    lower_current_id = 0
    for i in range(len(currents)):
        if currents[i] < current:
            lower_current_id = i

    upper_current_id = 0
    for i in range(len(currents)):
        if currents[i] > current:
            upper_current_id = i
            break

    current_weigth = (current - currents[lower_current_id]) / (currents[upper_current_id] - currents[lower_current_id])

    a = data_a[2 + lower_current_id]
    b = data_b[2 + upper_current_id]

    # Use current, to interpolate between datas
    return (
        distance * sign, # Distance
        lerp(data_a[1], data_b[1], current_weigth), # Inductance is not signed
        lerp(a * sign, b * sign, current_weigth) # Force
    )

def load_cgdata(coiltype):
    coil_data = []
    coil_desc = {}

    coilfile_base = "./Data/%s" % coiltype

    descFile = "%s.%s" % (coilfile_base, 'json')
    dataFile = "%s.%s" % (coilfile_base, 'csv')

    # Read JSON file
    f = open(descFile)
    coil_desc = json.load(f)
    f.close()

    # Read DATA file
    f = open(dataFile)
    csv_data = f.readlines()
    csv_data.remove(csv_data[0])
    f.close()

    # Parse CSV data
    for i in range(len(csv_data)):
        line = csv_data[i].replace(" ", "").split(",")

        distance = float(line[0])
        inductance = float(line[1])

        data_entry = []
        data_entry.append(distance)
        data_entry.append(inductance)
        
        for j in range(len(coil_desc['Currents'])):
            force = float(line[2 + j])
            data_entry.append(force)
            pass
        coil_data.append(data_entry)
        pass
        
    return [coil_data, coil_desc]