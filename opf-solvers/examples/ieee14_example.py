import sys
import os
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.opf.ac_opf import ACOPF
from src.visualization.opf_visualizer import OPFVisualizer
from src.test_cases.ieee14 import get_ieee14_case
from pyomo.environ import value

def main():
    # Get IEEE 14-bus case data
    case_data = get_ieee14_case()
    
    # Create and solve OPF problem
    opf = ACOPF(case_data)
    results = opf.solve()
    
    # Extract results using Pyomo's value() function
    solution = {
        'V': {b: value(opf.model.V[b]) for b in opf.model.B},
        'theta': {b: value(opf.model.theta[b]) for b in opf.model.B},
        'Pg': {g: value(opf.model.Pg[g]) for g in opf.model.G},
        'Qg': {g: value(opf.model.Qg[g]) for g in opf.model.G},
        'branch_flows': {}
    }
    
    # Calculate branch flows
    for idx, branch in case_data['branches'].iterrows():
        from_bus = int(branch['from_bus'])
        to_bus = int(branch['to_bus'])
        r = float(branch['r'])
        x = float(branch['x'])
        y = 1 / complex(r, x)
        v_from = solution['V'][from_bus]
        v_to = solution['V'][to_bus]
        theta_from = solution['theta'][from_bus]
        theta_to = solution['theta'][to_bus]
        flow = abs(v_from * v_to * y * 
                  (np.cos(theta_from - theta_to) + 
                   1j * np.sin(theta_from - theta_to)))
        solution['branch_flows'][idx] = flow
        
    # Create visualizer and plot results
    visualizer = OPFVisualizer(case_data, solution)
    
    # Create output directory if it doesn't exist
    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Generate and save plots
    visualizer.plot_voltage_profile(save_path=os.path.join(output_dir, 'voltage_profile.png'))
    visualizer.plot_power_flow(save_path=os.path.join(output_dir, 'power_flow.png'))
    visualizer.plot_generator_output(save_path=os.path.join(output_dir, 'generator_output.png'))
    visualizer.plot_constraint_violations(save_path=os.path.join(output_dir, 'constraint_violations.png'))
    
    # Print summary
    print("\nOPF Solution Summary:")
    print(f"Total Generation Cost: {sum(solution['Pg'].values()):.2f} MW")
    print(f"Total Real Power Generation: {sum(solution['Pg'].values()):.2f} MW")
    print(f"Total Reactive Power Generation: {sum(solution['Qg'].values()):.2f} MVAr")

if __name__ == "__main__":
    main() 