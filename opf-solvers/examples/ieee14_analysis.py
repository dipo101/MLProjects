import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.opf.ac_opf import ACOPF
from src.analysis.solver_comparison import SolverComparison
from src.visualization.power_system_visualizer import PowerSystemVisualizer
import pandas as pd
import matplotlib.pyplot as plt
from src.data.case_reader import read_ieee_case

def main():
    # Create results directory if it doesn't exist
    results_dir = "results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
        
    # Load IEEE 14-bus case data
    print("Loading IEEE 14-bus case data...")
    case_data = read_ieee_case('ieee14')
    
    # Initialize the OPF problem
    print("Initializing OPF problem...")
    opf = ACOPF(case_data)
    
    # Run solver comparison
    print("Running solver comparison...")
    comparison = SolverComparison(case_data)
    
    # Define solvers to compare
    solvers = ['ipopt', 'gams']  # We'll use GAMS with different solvers
    
    # Define solver options
    solver_options = {
        'ipopt': {
            'tol': 1e-6,
            'max_iter': 1000,
            'print_level': 5
        },
        'gams': {
            'solver': 'conopt',  # Try different GAMS solvers: conopt, snopt, minos
            'io_options': {
                'solver': 'conopt',
                'add_options': ['GAMS_MODEL.optfile = 1;']
            }
        }
    }
    
    # Run comparison
    results_df = comparison.run_comparison(solvers, solver_options)
    
    # Save comparison results
    comparison.save_comparison_results(results_df, f"{results_dir}/solver_comparison.csv")
    
    # Plot comparison
    comparison.plot_comparison(results_df, f"{results_dir}/solver_comparison.png")
    
    # Create visualizations
    print("\nCreating visualizations...")
    visualizer = PowerSystemVisualizer(opf)
    
    # Create dashboard of all visualizations
    visualizer.create_dashboard(results_dir)
    
    # Print summary
    print("\nAnalysis complete! Results saved in the 'results' directory:")
    print("- solver_comparison.csv: Detailed solver comparison results")
    print("- solver_comparison.png: Solver comparison plots")
    print("- voltage_profile.png: Bus voltage profile")
    print("- branch_flows.png: Branch flow magnitudes")
    print("- generation_dispatch.png: Generator dispatch")
    print("- network_topology.png: Network topology with flows")
    print("- constraint_violations.png: Any constraint violations")

if __name__ == "__main__":
    main() 