import numpy as np
import pandas as pd

def get_ieee14_case():
    """
    Returns the IEEE 14-bus test case data
    
    Returns:
        dict: Dictionary containing bus, branch, and generator data
    """
    # Bus data
    bus_data = {
        'bus': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
        'type': [3, 2, 2, 1, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1],
        'Pd': [0.0, 21.7, 94.2, 47.8, 7.6, 11.2, 0.0, 0.0, 29.5, 9.0, 3.5, 6.1, 13.5, 14.9],
        'Qd': [0.0, 12.7, 19.0, -3.9, 1.6, 7.5, 0.0, 0.0, 16.6, 5.8, 1.8, 1.6, 5.8, 5.0],
        'Gs': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'Bs': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'Vmax': [1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1],
        'Vmin': [0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9]
    }
    buses = pd.DataFrame(bus_data).set_index('bus')
    
    # Generator data
    gen_data = {
        'bus': [1, 2, 3, 6, 8],
        'Pmax': [332.4, 140.0, 100.0, 100.0, 100.0],
        'Pmin': [0.0, 0.0, 0.0, 0.0, 0.0],
        'Qmax': [10.0, 50.0, 40.0, 24.0, 24.0],
        'Qmin': [-10.0, -50.0, -40.0, -24.0, -24.0],
        'Vg': [1.06, 1.045, 1.01, 1.07, 1.09],
        'mBase': [100.0, 100.0, 100.0, 100.0, 100.0]
    }
    generators = pd.DataFrame(gen_data).set_index('bus')
    
    # Branch data
    branch_data = {
        'from_bus': [1, 1, 2, 2, 2, 3, 4, 4, 5, 6, 6, 6, 7, 7, 9, 9, 10, 12, 13],
        'to_bus': [2, 5, 3, 4, 5, 4, 5, 7, 6, 11, 12, 13, 8, 9, 10, 14, 11, 13, 14],
        'r': [0.01938, 0.05403, 0.04699, 0.05811, 0.05695, 0.06701, 0.01335, 0.0, 0.0, 0.09498, 0.12291, 0.06615, 0.0, 0.0, 0.03181, 0.12711, 0.08205, 0.22092, 0.17093],
        'x': [0.05917, 0.22304, 0.19797, 0.17632, 0.17388, 0.17103, 0.04211, 0.25202, 0.20912, 0.19890, 0.25581, 0.13027, 0.17615, 0.11001, 0.08450, 0.27038, 0.19207, 0.19988, 0.34802],
        'b': [0.0528, 0.0492, 0.0438, 0.0374, 0.0340, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'rate_a': [175.0, 175.0, 175.0, 175.0, 175.0, 175.0, 175.0, 175.0, 175.0, 175.0, 175.0, 175.0, 175.0, 175.0, 175.0, 175.0, 175.0, 175.0, 175.0]
    }
    branches = pd.DataFrame(branch_data)
    
    # Create Ybus matrix
    n_buses = len(buses)
    Ybus = np.zeros((n_buses, n_buses), dtype=complex)
    
    for _, branch in branches.iterrows():
        i = int(branch['from_bus']) - 1  # Convert to 0-based indexing
        j = int(branch['to_bus']) - 1
        r = float(branch['r'])
        x = float(branch['x'])
        b = float(branch['b'])
        y = 1 / complex(r, x)
        Ybus[i, j] = -y
        Ybus[j, i] = -y
        Ybus[i, i] += y + 1j * b/2
        Ybus[j, j] += y + 1j * b/2
        
    return {
        'buses': buses,
        'generators': generators,
        'branches': branches,
        'Ybus': Ybus
    } 