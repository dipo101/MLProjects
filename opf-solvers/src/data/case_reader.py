import numpy as np
import pandas as pd
from typing import Dict, Any

def read_ieee_case(case_name: str) -> Dict[str, Any]:
    """
    Read IEEE test case data.
    
    Args:
        case_name: Name of the test case (e.g., 'ieee14')
        
    Returns:
        Dictionary containing case data
    """
    if case_name == 'ieee14':
        # IEEE 14-bus test case data
        data = {
            'buses': list(range(1, 15)),  # 14 buses
            'generators': [1, 2, 3, 6, 8],  # 5 generators
            'branches': [
                (1, 2), (1, 5), (2, 3), (2, 4), (2, 5),
                (3, 4), (4, 5), (4, 7), (4, 9), (5, 6),
                (6, 11), (6, 12), (6, 13), (7, 8), (7, 9),
                (9, 10), (9, 14), (10, 11), (12, 13), (13, 14)
            ],
            'Pd': {  # Load real power demand (MW)
                2: 21.7, 3: 94.2, 4: 47.8, 5: 7.6, 6: 11.2,
                9: 29.5, 10: 9.0, 11: 3.5, 12: 6.1, 13: 13.5, 14: 14.9
            },
            'Qd': {  # Load reactive power demand (MVAr)
                2: 12.7, 3: 19.0, 4: -3.9, 5: 1.6, 6: 7.5,
                9: 16.6, 10: 5.8, 11: 1.8, 12: 1.6, 13: 5.8, 14: 5.0
            },
            'Pg_max': {  # Maximum real power generation (MW)
                1: 332.4, 2: 140.0, 3: 100.0, 6: 100.0, 8: 100.0
            },
            'Pg_min': {  # Minimum real power generation (MW)
                1: 0.0, 2: 0.0, 3: 0.0, 6: 0.0, 8: 0.0
            },
            'Qg_max': {  # Maximum reactive power generation (MVAr)
                1: 10.0, 2: 50.0, 3: 40.0, 6: 24.0, 8: 24.0
            },
            'Qg_min': {  # Minimum reactive power generation (MVAr)
                1: -10.0, 2: -40.0, 3: -40.0, 6: -6.0, 8: -6.0
            },
            'V_max': {bus: 1.05 for bus in range(1, 15)},  # Maximum voltage magnitude
            'V_min': {bus: 0.95 for bus in range(1, 15)},  # Minimum voltage magnitude
            'branch_x': {  # Branch reactance (p.u.)
                (1, 2): 0.05917, (1, 5): 0.22304, (2, 3): 0.19797,
                (2, 4): 0.17632, (2, 5): 0.17388, (3, 4): 0.17103,
                (4, 5): 0.04211, (4, 7): 0.20912, (4, 9): 0.55618,
                (5, 6): 0.25202, (6, 11): 0.19890, (6, 12): 0.25581,
                (6, 13): 0.13027, (7, 8): 0.17615, (7, 9): 0.11001,
                (9, 10): 0.08450, (9, 14): 0.27038, (10, 11): 0.19207,
                (12, 13): 0.19988, (13, 14): 0.34802
            },
            'branch_r': {  # Branch resistance (p.u.)
                (1, 2): 0.01938, (1, 5): 0.05403, (2, 3): 0.04699,
                (2, 4): 0.05811, (2, 5): 0.05695, (3, 4): 0.06701,
                (4, 5): 0.01335, (4, 7): 0.00000, (4, 9): 0.00000,
                (5, 6): 0.00000, (6, 11): 0.09498, (6, 12): 0.12291,
                (6, 13): 0.06615, (7, 8): 0.00000, (7, 9): 0.00000,
                (9, 10): 0.03181, (9, 14): 0.12711, (10, 11): 0.08205,
                (12, 13): 0.22092, (13, 14): 0.17093
            },
            'Sij_max': {branch: 100.0 for branch in [  # Branch flow limits (MVA)
                (1, 2), (1, 5), (2, 3), (2, 4), (2, 5),
                (3, 4), (4, 5), (4, 7), (4, 9), (5, 6),
                (6, 11), (6, 12), (6, 13), (7, 8), (7, 9),
                (9, 10), (9, 14), (10, 11), (12, 13), (13, 14)
            ]},
            'base_mva': 100.0  # Base MVA
        }
        
        # Add reverse branches with same parameters
        branches_list = list(data['branches'])
        for (i, j) in branches_list:
            data['branch_r'][(j, i)] = data['branch_r'][(i, j)]
            data['branch_x'][(j, i)] = data['branch_x'][(i, j)]
            data['Sij_max'][(j, i)] = data['Sij_max'][(i, j)]
            data['branches'].append((j, i))
            
        return data
    else:
        raise ValueError(f"Unknown case name: {case_name}") 