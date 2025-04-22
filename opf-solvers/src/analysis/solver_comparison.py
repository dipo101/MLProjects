import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional
from pyomo.environ import SolverFactory, value
from ..opf.ac_opf import ACOPF
import os
import pyomo as pyo
import tempfile
import shutil
import re

class SolverComparison:
    """Class for comparing different solvers for the AC OPF problem."""
    
    def __init__(self, case_data):
        """Initialize the solver comparison.
        
        Args:
            case_data: The case data for the power system.
        """
        self.case_data = case_data
        self.opf = ACOPF(case_data)
        self.results_dir = 'results'
        os.makedirs(self.results_dir, exist_ok=True)
    
    def run_comparison(self, solvers=None, solver_options=None):
        """Run the OPF problem with different solvers and compare results.
        
        Args:
            solvers (list, optional): List of solver names to try. Defaults to ['ipopt', 'gams'].
            solver_options (dict, optional): Dictionary of solver-specific options. Defaults to None.
        
        Returns:
            pd.DataFrame: DataFrame containing solver comparison results.
        """
        if solvers is None:
            solvers = ['ipopt', 'gams']  # Default solvers
            
        if solver_options is None:
            solver_options = {}
            
        comparison_data = []
        
        for solver_name in solvers:
            try:
                print(f"\nRunning {solver_name}...")
                
                if solver_name == 'gams':
                    # Try different GAMS solvers
                    gams_solvers = ['conopt', 'snopt', 'minos']
                    for gams_solver in gams_solvers:
                        print(f"  Trying GAMS solver: {gams_solver}")
                        try:
                            # Create parameter files for GAMS solvers
                            temp_dir = tempfile.mkdtemp()
                            
                            # Create solver option file
                            opt_file = os.path.join(temp_dir, f'{gams_solver}.opt')
                            with open(opt_file, 'w') as f:
                                if gams_solver == 'conopt':
                                    f.write('Tol_Optimality 1.0e-6\n')
                                    f.write('Tol_Feasibility 1.0e-6\n')
                                elif gams_solver == 'snopt':
                                    f.write('Major feasibility tolerance 1.0e-6\n')
                                    f.write('Major optimality tolerance 1.0e-6\n')
                                elif gams_solver == 'minos':
                                    f.write('Feasibility tolerance 1.0e-6\n')
                                    f.write('Optimality tolerance 1.0e-6\n')
                            
                            # Set up solver options
                            solver_options = {
                                'solver': gams_solver,
                                'tmpdir': temp_dir
                            }
                            
                            # Time the solver execution
                            start_time = time.time()
                            results = self.opf.solve(solver='gams', solver_options=solver_options)
                            solve_time = time.time() - start_time
                            
                            print(f"  Completed {gams_solver} in {solve_time:.2f} seconds")
                            
                            # Extract metrics from solver output
                            metrics = {
                                'solver': f'gams_{gams_solver}',
                                'solve_time': solve_time,
                                'objective_value': results.get('objective_value'),
                                'constraint_violation': results.get('constraint_violation'),
                                'dual_infeasibility': results.get('dual_infeasibility'),
                                'iterations': results.get('iterations'),
                                'status': results.get('status'),
                                'termination_condition': results.get('termination_condition')
                            }
                            
                            # Parse solver output for specific metrics
                            solver_output = results.get('Solver', {}).get('Output', '')
                            if gams_solver == 'conopt':
                                if 'Optimal solution' in solver_output:
                                    metrics['status'] = 'optimal'
                                if 'iterations' in solver_output.lower():
                                    try:
                                        metrics['iterations'] = int(re.search(r'iterations:\s*(\d+)', solver_output.lower()).group(1))
                                    except:
                                        pass
                            elif gams_solver == 'snopt':
                                if 'Optimal solution found' in solver_output:
                                    metrics['status'] = 'optimal'
                                if 'iterations' in solver_output.lower():
                                    try:
                                        metrics['iterations'] = int(re.search(r'iterations:\s*(\d+)', solver_output.lower()).group(1))
                                    except:
                                        pass
                            elif gams_solver == 'minos':
                                if 'Optimal Solution found' in solver_output:
                                    metrics['status'] = 'optimal'
                                if 'iterations' in solver_output.lower():
                                    try:
                                        metrics['iterations'] = int(re.search(r'iterations:\s*(\d+)', solver_output.lower()).group(1))
                                    except:
                                        pass
                            
                            comparison_data.append(metrics)
                            
                        except Exception as e:
                            print(f"  Error running GAMS with {gams_solver}: {str(e)}")
                            comparison_data.append({
                                'solver': f'gams_{gams_solver}',
                                'solve_time': None,
                                'objective_value': None,
                                'constraint_violation': None,
                                'dual_infeasibility': None,
                                'iterations': None,
                                'status': 'error',
                                'termination_condition': str(e)
                            })
                else:
                    # Handle other solvers (like IPOPT)
                    solver = SolverFactory(solver_name)
                    
                    if not solver.available():
                        print(f"Solver {solver_name} is not available, skipping...")
                        continue
                        
                    # Time the solver execution
                    start_time = time.time()
                    results = self.opf.solve(solver=solver_name, 
                                           solver_options=solver_options.get(solver_name, {}))
                    solve_time = time.time() - start_time
                    
                    print(f"Completed {solver_name} in {solve_time:.2f} seconds")
                    
                    # Extract metrics from results
                    metrics = {
                        'solver': solver_name,
                        'solve_time': solve_time,
                        'objective_value': results.get('objective_value'),
                        'constraint_violation': results.get('constraint_violation'),
                        'dual_infeasibility': results.get('dual_infeasibility'),
                        'iterations': results.get('iterations'),
                        'status': results.get('status'),
                        'termination_condition': results.get('termination_condition')
                    }
                    
                    comparison_data.append(metrics)
                
            except Exception as e:
                print(f"Error running {solver_name}: {str(e)}")
                comparison_data.append({
                    'solver': solver_name,
                    'solve_time': None,
                    'objective_value': None,
                    'constraint_violation': None,
                    'dual_infeasibility': None,
                    'iterations': None,
                    'status': 'error',
                    'termination_condition': str(e)
                })
        
        # Convert to DataFrame and sort by solve time
        df = pd.DataFrame(comparison_data)
        if not df.empty:
            df = df.sort_values('solve_time')
        return df
        
    def plot_comparison(self, df: pd.DataFrame, save_path: str = None):
        """Plot comparison of solver performance metrics."""
        
        sns.set_style("whitegrid")
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()
        
        # Plot solve time
        sns.barplot(data=df, x='solver', y='solve_time', ax=axes[0])
        axes[0].set_title('Solve Time (s)')
        axes[0].set_ylabel('Time (s)')
        
        # Plot objective value
        sns.barplot(data=df, x='solver', y='objective_value', ax=axes[1])
        axes[1].set_title('Objective Value')
        axes[1].ticklabel_format(style='sci', axis='y', scilimits=(0,0))
        
        # Plot constraint violation
        sns.barplot(data=df, x='solver', y='constraint_violation', ax=axes[2])
        axes[2].set_title('Constraint Violation')
        axes[2].ticklabel_format(style='sci', axis='y', scilimits=(0,0))
        
        # Plot iterations
        sns.barplot(data=df, x='solver', y='iterations', ax=axes[3])
        axes[3].set_title('Number of Iterations')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight', dpi=300)
        else:
            plt.show()
            
    def save_comparison_results(self, df: pd.DataFrame, filepath: str):
        """
        Save comparison results to a CSV file.
        
        Args:
            df: DataFrame containing comparison results
            filepath: Path to save the CSV file
        """
        df.to_csv(filepath, index=False)

    def run_solver_comparison(self, solvers=None, solver_options=None):
        """Run solver comparison and return results as a DataFrame.
        
        Args:
            solvers (list): List of solver names to compare. Defaults to ['ipopt'].
            solver_options (dict): Dictionary of solver-specific options. Defaults to None.
        
        Returns:
            pd.DataFrame: DataFrame containing solver comparison results.
        """
        if solvers is None:
            solvers = ['ipopt']
        if solver_options is None:
            solver_options = {}
        
        comparison_data = []
        
        for solver in solvers:
            try:
                print(f"\nRunning {solver}...")
                start_time = time.time()
                
                # Get solver-specific options
                options = solver_options.get(solver, {})
                
                # Use the solve method from ACOPF class instead of creating a separate solver instance
                results = self.case_data.solve(solver, options)
                solve_time = time.time() - start_time
                
                # Create metrics dictionary from returned results
                metrics = {
                    'solver': solver,
                    'solve_time': solve_time,
                    'objective_value': results.get('objective_value'),
                    'constraint_violation': results.get('constraint_violation'),
                    'dual_infeasibility': results.get('dual_infeasibility'),
                    'iterations': results.get('iterations'),
                    'status': results.get('status'),
                    'termination_condition': results.get('termination_condition')
                }
                
                comparison_data.append(metrics)
                print(f"Completed {solver} in {solve_time:.2f} seconds")
                
            except Exception as e:
                print(f"Error running {solver}: {str(e)}")
                comparison_data.append({
                    'solver': solver,
                    'solve_time': None,
                    'objective_value': None,
                    'constraint_violation': None,
                    'dual_infeasibility': None,
                    'iterations': None,
                    'status': 'error',
                    'termination_condition': str(e)
                })
        
        # Convert to DataFrame and save results
        df = pd.DataFrame(comparison_data)
        
        # Make sure results_dir is defined
        if not hasattr(self, 'results_dir'):
            self.results_dir = 'results'
            
        os.makedirs(self.results_dir, exist_ok=True)
        df.to_csv(os.path.join(self.results_dir, 'solver_comparison.csv'), index=False)
        return df 