from pyomo.environ import (
    ConcreteModel, Set, Param, Var, Constraint,
    Objective, minimize, value, SolverFactory, cos as pyo_cos, sin as pyo_sin
)
from pyomo.core.base.PyomoModel import ConcreteModel
from pyomo.opt import SolverStatus, TerminationCondition
import numpy as np
import pandas as pd
import time

class ACOPF:
    def __init__(self, case_data):
        """
        Initialize AC OPF problem with case data
        
        Args:
            case_data (dict): Dictionary containing bus, branch, and generator data
        """
        self.case_data = case_data
        self.model = ConcreteModel()
        self._create_basic_sets()
        self._create_parameters()
        self._create_variables()
        self._set_initial_conditions()
        self._create_objective()
        self._create_constraints()
        
    def _create_basic_sets(self):
        """Create basic sets for buses, generators, and branches"""
        m = self.model
        
        # Create basic sets
        m.B = Set(initialize=self.case_data['buses'])  # Buses
        m.G = Set(initialize=self.case_data['generators'])  # Generators
        m.L = Set(initialize=self.case_data['branches'])  # Branches
        
    def _create_parameters(self):
        """Create parameters for the OPF problem"""
        m = self.model
        
        # Bus parameters
        def pd_init(m, b):
            return self.case_data['Pd'].get(b, 0.0)
        m.Pd = Param(m.B, initialize=pd_init)
        
        def qd_init(m, b):
            return self.case_data['Qd'].get(b, 0.0)
        m.Qd = Param(m.B, initialize=qd_init)
        
        def vmax_init(m, b):
            return self.case_data['V_max'][b]
        m.V_max = Param(m.B, initialize=vmax_init)
        
        def vmin_init(m, b):
            return self.case_data['V_min'][b]
        m.V_min = Param(m.B, initialize=vmin_init)
        
        # Generator parameters
        def pg_max_init(m, g):
            return self.case_data['Pg_max'][g]
        m.Pg_max = Param(m.G, initialize=pg_max_init)
        
        def pg_min_init(m, g):
            return self.case_data['Pg_min'][g]
        m.Pg_min = Param(m.G, initialize=pg_min_init)
        
        def qg_max_init(m, g):
            return self.case_data['Qg_max'][g]
        m.Qg_max = Param(m.G, initialize=qg_max_init)
        
        def qg_min_init(m, g):
            return self.case_data['Qg_min'][g]
        m.Qg_min = Param(m.G, initialize=qg_min_init)
        
        # Branch parameters
        def branch_r_init(m, i, j):
            return self.case_data['branch_r'][(i, j)]
        m.branch_r = Param(m.L, initialize=branch_r_init)
        
        def branch_x_init(m, i, j):
            return self.case_data['branch_x'][(i, j)]
        m.branch_x = Param(m.L, initialize=branch_x_init)
        
        def sij_max_init(m, i, j):
            return self.case_data['Sij_max'][(i, j)]
        m.Sij_max = Param(m.L, initialize=sij_max_init)
        
    def _create_variables(self):
        """Create decision variables"""
        m = self.model
        
        # Voltage magnitude and angle
        m.V = Var(m.B, bounds=(0.95, 1.05), initialize=1.0)
        m.theta = Var(m.B, bounds=(-np.pi/2, np.pi/2), initialize=0.0)
        
        # Generator real and reactive power
        m.Pg = Var(m.G, initialize=lambda m, g: m.Pg_min[g])
        m.Qg = Var(m.G, initialize=lambda m, g: 0.0)
        
        # Branch power flows
        m.Pij = Var(m.L, bounds=(-1000, 1000), initialize=0.0)
        m.Qij = Var(m.L, bounds=(-1000, 1000), initialize=0.0)
        
        # Slack variables for power balance
        m.slack_p = Var(m.B, bounds=(-1e3, 1e3), initialize=0.0)
        m.slack_q = Var(m.B, bounds=(-1e3, 1e3), initialize=0.0)
        
    def _set_initial_conditions(self):
        """Set initial conditions for variables"""
        m = self.model
        
        # Set initial voltage magnitudes
        for b in m.B:
            m.V[b] = 1.0
                
        # Set initial voltage angles (flat start)
        for b in m.B:
            m.theta[b] = 0.0
            
        # Set initial generator outputs based on load distribution
        total_load = sum(value(m.Pd[b]) for b in m.B)
        num_gens = len(m.G)
        avg_gen = total_load / num_gens if num_gens > 0 else 0
        
        # Distribute load among generators
        remaining_load = total_load
        for g in m.G:
            pg_max = value(m.Pg_max[g])
            if g == list(m.G)[-1]:  # Last generator takes remaining load
                pg = min(remaining_load, pg_max)
            else:
                pg = min(avg_gen, pg_max)
                remaining_load -= pg
            m.Pg[g] = pg
            
            # Initialize reactive power to zero
            m.Qg[g] = 0.0
            
        # Initialize branch flows using DC approximation
        for (i, j) in m.L:
            x = value(m.branch_x[(i, j)])
            if x != 0:
                m.Pij[(i, j)] = (value(m.theta[i]) - value(m.theta[j])) / x
            else:
                m.Pij[(i, j)] = 0.0
            m.Qij[(i, j)] = 0.0  # Start with zero reactive power flow
        
    def _create_objective(self):
        """Create objective function (minimize generation cost + penalties)"""
        m = self.model
        
        def obj_rule(m):
            gen_cost = sum(0.1 * m.Pg[g] * m.Pg[g] + 10 * m.Pg[g] for g in m.G)
            slack_penalty = 1e6 * (sum(m.slack_p[b]**2 + m.slack_q[b]**2 for b in m.B))
            return gen_cost + slack_penalty
        
        m.obj = Objective(rule=obj_rule, sense=minimize)
        
    def _create_constraints(self):
        """Create all constraints for the AC OPF problem."""
        m = self.model
        
        # Power balance constraints
        def power_balance_real_rule(m, b):
            gen_power = sum(m.Pg[g] for g in m.G if g == b)
            branch_power = sum(m.Pij[l] for l in m.L if l[0] == b) - sum(m.Pij[l] for l in m.L if l[1] == b)
            return gen_power - m.Pd[b] + m.slack_p[b] == branch_power
        m.power_balance_real = Constraint(m.B, rule=power_balance_real_rule)
        
        def power_balance_reactive_rule(m, b):
            gen_power = sum(m.Qg[g] for g in m.G if g == b)
            branch_power = sum(m.Qij[l] for l in m.L if l[0] == b) - sum(m.Qij[l] for l in m.L if l[1] == b)
            return gen_power - m.Qd[b] + m.slack_q[b] == branch_power
        m.power_balance_reactive = Constraint(m.B, rule=power_balance_reactive_rule)
        
        # Voltage bounds
        def voltage_bounds_rule(m, b):
            return (m.V_min[b], m.V[b], m.V_max[b])
        m.voltage_bounds = Constraint(m.B, rule=voltage_bounds_rule)
        
        # Generator limits
        def generator_p_limits_rule(m, g):
            return (m.Pg_min[g], m.Pg[g], m.Pg_max[g])
        m.generator_p_limits = Constraint(m.G, rule=generator_p_limits_rule)
        
        def generator_q_limits_rule(m, g):
            return (m.Qg_min[g], m.Qg[g], m.Qg_max[g])
        m.generator_q_limits = Constraint(m.G, rule=generator_q_limits_rule)
        
        # Branch flow equations
        def branch_flow_p_rule(m, i, j):
            g = m.branch_r[(i, j)] / (m.branch_r[(i, j)]**2 + m.branch_x[(i, j)]**2)
            b = -m.branch_x[(i, j)] / (m.branch_r[(i, j)]**2 + m.branch_x[(i, j)]**2)
            
            return m.Pij[(i, j)] == \
                m.V[i] * m.V[j] * (g * pyo_cos(m.theta[i] - m.theta[j]) +
                                  b * pyo_sin(m.theta[i] - m.theta[j])) - \
                (g * m.V[i]**2)
        m.branch_flow_p = Constraint(m.L, rule=branch_flow_p_rule)
        
        def branch_flow_q_rule(m, i, j):
            g = m.branch_r[(i, j)] / (m.branch_r[(i, j)]**2 + m.branch_x[(i, j)]**2)
            b = -m.branch_x[(i, j)] / (m.branch_r[(i, j)]**2 + m.branch_x[(i, j)]**2)
            
            return m.Qij[(i, j)] == \
                m.V[i] * m.V[j] * (g * pyo_sin(m.theta[i] - m.theta[j]) -
                                  b * pyo_cos(m.theta[i] - m.theta[j])) + \
                (b * m.V[i]**2)
        m.branch_flow_q = Constraint(m.L, rule=branch_flow_q_rule)
        
        # Branch flow limits
        def branch_flow_limits_rule(m, i, j):
            return m.Pij[(i, j)]**2 + m.Qij[(i, j)]**2 <= m.Sij_max[(i, j)]**2
        m.branch_flow_limits = Constraint(m.L, rule=branch_flow_limits_rule)
        
    def solve(self, solver='ipopt', solver_options=None):
        """Solve the AC OPF problem using the specified solver.

        Args:
            solver (str): The solver to use (default: 'ipopt')
            solver_options (dict): Additional solver options (default: None)

        Returns:
            dict: Solution results including status, objective value, and metrics
        """
        try:
            # Set default solver options if none provided
            if solver_options is None:
                solver_options = {
                    'max_iter': 1000,
                    'tol': 1e-6,
                    'linear_solver': 'mumps'
                }

            # Create the solver
            opt = SolverFactory(solver)
            for key, value in solver_options.items():
                opt.options[key] = value

            # Solve the model and measure time
            t0 = time.time()
            log_file = solver+'_output.log'
            if(solver == 'gams'):
                log_file = solver_options["solver"] + "_"+log_file
            results = opt.solve(self.model, tee=True, logfile=log_file)
            solve_time = results.solver.time if solver != 'gams' else time.time() - t0

            self.model.solutions.store_to(results)

            # Check if solver was successful
            if (results.solver.status == SolverStatus.ok and 
                (results.solver.termination_condition == TerminationCondition.optimal or 
                 results.solver.termination_condition == TerminationCondition.locallyOptimal)):
                # Get objective value
                try:
                    obj_value = results.solution[0].objective['obj']['Value']
                except:
                    obj_value = None

                # Initialize metrics dictionary for successful solve
                metrics = {
                    'status': str(results.solver.status),
                    'termination_condition': str(results.solver.termination_condition),
                    'solve_time': solve_time,
                    'objective_value': obj_value,
                    'constraint_violation': None,
                    'dual_infeasibility': None,
                    'iterations': None
                }

                # Handle IPOPT results
                if solver == 'ipopt':
                    try:
                        with open(log_file, 'r') as f:
                            log_content = f.read()
                            
                            # Extract number of iterations
                            if 'Number of Iterations....:' in log_content:
                                metrics['iterations'] = int(log_content.split('Number of Iterations....:')[1].split('\n')[0].strip())
                                
                            # Extract constraint violation and dual infeasibility
                            if 'Constraint violation....:' in log_content:
                                metrics['constraint_violation'] = float(log_content.split('Constraint violation....:')[1].split('\n')[0].split()[0])
                                
                            if 'Dual infeasibility......:' in log_content:
                                metrics['dual_infeasibility'] = float(log_content.split('Dual infeasibility......:')[1].split('\n')[0].split()[0])
                    except Exception as e:
                        print(f"Could not read IPOPT metrics from logfile: {str(e)}")

                # Handle GAMS results
                elif solver == 'gams':
                    try:
                        with open(log_file, 'r') as f:
                            log_content = f.read()
                            
                            # Extract iterations based on solver type
                            if 'conopt' in solver_options.get('solver', '').lower():
                                # CONOPT reports iterations in a table format with columns:
                                # Iter Phase   Ninf   Infeasibility   RGmax      NSB   Step  InItr MX OK
                                lines = log_content.split('\n')
                                
                                # Find the last iteration line
                                last_iter_line = None
                                for line in reversed(lines):
                                    if line.strip() and line.strip()[0].isdigit():
                                        parts = line.split()
                                        if len(parts) >= 2 and parts[0].isdigit():
                                            last_iter_line = line
                                            break
                                
                                if last_iter_line:
                                    parts = last_iter_line.split()
                                    metrics['iterations'] = int(parts[0])
                                    if len(parts) >= 5:
                                        metrics['dual_infeasibility'] = float(parts[4])  # RGmax
                                
                                # First check for "Feasible solution" message
                                for line in lines:
                                    if 'Feasible solution' in line:
                                        metrics['constraint_violation'] = 0.0
                                        break
                                
                                # If no feasible solution found, look for infeasibility value
                                if metrics['constraint_violation'] is None:
                                    for line in reversed(lines):
                                        if 'Infeasibility' in line:
                                            next_line = lines[lines.index(line) + 1]
                                            if next_line.strip():
                                                parts = next_line.split()
                                                if len(parts) >= 4:
                                                    metrics['constraint_violation'] = float(parts[3])
                                                break
                                
                            elif 'snopt' in solver_options.get('solver', '').lower():
                                # SNOPT reports iterations
                                if 'No. of iterations' in log_content:
                                    metrics['iterations'] = int(log_content.split('No. of iterations')[1].split()[0])
                                # SNOPT reports primal and dual infeasibility
                                if 'Max Primal infeas' in log_content:
                                    metrics['constraint_violation'] = float(log_content.split('Max Primal infeas')[1].split()[0])
                                if 'Max Dual infeas' in log_content:
                                    metrics['dual_infeasibility'] = float(log_content.split('Max Dual infeas')[1].split()[0])
                                
                            elif 'minos' in solver_options.get('solver', '').lower():
                                # MINOS reports total iterations in "Itn  ninf" format
                                lines = log_content.split('\n')
                                for line in lines:
                                    if line.strip().startswith('Itn'):
                                        # Look for the next line which contains the iteration count
                                        next_line = lines[lines.index(line) + 1]
                                        if next_line.strip():
                                            metrics['iterations'] = int(next_line.split()[0])
                                            break
                                
                                # MINOS reports feasibility and optimality in the major iteration lines
                                # Find all major iteration lines
                                major_iter_lines = []
                                for i, line in enumerate(lines):
                                    if line.strip().startswith('Major minor'):
                                        # Look for the next line which contains the actual iteration data
                                        next_line = lines[i + 1]
                                        if next_line.strip() and next_line.strip()[0].isdigit():
                                            # Keep looking for more iteration lines until we hit a non-digit line
                                            current_line = next_line
                                            while True:
                                                next_next_line = lines[lines.index(current_line) + 1]
                                                if next_next_line.strip() and next_next_line.strip()[0].isdigit():
                                                    current_line = next_next_line
                                                else:
                                                    break
                                            major_iter_lines.append(current_line)
                                
                                # Get the last major iteration line
                                if major_iter_lines:
                                    last_major_line = major_iter_lines[-1]
                                    parts = last_major_line.split()
                                    if len(parts) >= 6:
                                        # The format is: major minor step objective Feasible Optimal nsb ncon penalty BSswp
                                        metrics['constraint_violation'] = float(parts[4])  # Feasible column
                                        metrics['dual_infeasibility'] = float(parts[5])   # Optimal column
                                
                    except Exception as e:
                        print(f"Could not read GAMS metrics from logfile: {str(e)}")

            else:
                # Initialize metrics dictionary for unsuccessful solve
                metrics = {
                    'status': str(results.solver.status),
                    'termination_condition': str(results.solver.termination_condition),
                    'solve_time': solve_time,
                    'objective_value': None,
                    'constraint_violation': None,
                    'dual_infeasibility': None,
                    'iterations': None
                }

            return metrics

        except Exception as e:
            print(f"Error solving OPF: {str(e)}")
            return {
                'status': 'error',
                'termination_condition': str(e),
                'solve_time': None,
                'objective_value': None,
                'constraint_violation': None,
                'dual_infeasibility': None,
                'iterations': None
            }