import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple
import networkx as nx
from ..opf.ac_opf import ACOPF

class PowerSystemVisualizer:
    """Class for visualizing power system states and constraints."""
    
    def __init__(self, opf_problem: ACOPF):
        """
        Initialize the visualizer.
        
        Args:
            opf_problem: An instance of ACOPF with the problem already solved
        """
        self.opf = opf_problem
        self.model = opf_problem.model
        self.buses = [b for b in self.model.B]
        self.generators = [g for g in self.model.G]
        self.branches = [(i,j) for (i,j) in self.model.L]
        
        # Helper function to safely get value
        def get_value(param):
            try:
                if param is None:
                    return None
                if hasattr(param, 'value'):
                    try:
                        val = param.value
                        if val is None and hasattr(param, 'get_value'):
                            val = param.get_value()
                        return val
                    except:
                        return None
                return param
            except:
                return None
            
        # Store variable values
        self.values = {
            'V': {b: get_value(self.model.V[b]) for b in self.buses},
            'theta': {b: get_value(self.model.theta[b]) for b in self.buses},
            'Pg': {g: get_value(self.model.Pg[g]) for g in self.generators},
            'Qg': {g: get_value(self.model.Qg[g]) for g in self.generators},
            'Pij': {(i,j): get_value(self.model.Pij[(i,j)]) for (i,j) in self.branches},
            'Qij': {(i,j): get_value(self.model.Qij[(i,j)]) for (i,j) in self.branches},
            'V_min': {b: get_value(self.model.V_min[b]) for b in self.buses},
            'V_max': {b: get_value(self.model.V_max[b]) for b in self.buses},
            'Pg_min': {g: get_value(self.model.Pg_min[g]) for g in self.generators},
            'Pg_max': {g: get_value(self.model.Pg_max[g]) for g in self.generators},
            'Qg_min': {g: get_value(self.model.Qg_min[g]) for g in self.generators},
            'Qg_max': {g: get_value(self.model.Qg_max[g]) for g in self.generators},
            'Sij_max': {(i,j): get_value(self.model.Sij_max[(i,j)]) for (i,j) in self.branches}
        }
        
    def plot_voltage_profile(self, save_path: Optional[str] = None):
        """
        Plot the voltage profile across all buses.
        
        Args:
            save_path: Optional path to save the plot
        """
        # Create DataFrame for plotting
        df = pd.DataFrame({
            'Bus': list(self.values['V'].keys()),
            'Voltage (p.u.)': list(self.values['V'].values())
        })
        
        # Plot
        plt.figure(figsize=(12, 6))
        sns.barplot(x='Bus', y='Voltage (p.u.)', data=df)
        plt.axhline(y=1.05, color='r', linestyle='--', label='Upper Limit')
        plt.axhline(y=0.95, color='r', linestyle='--', label='Lower Limit')
        plt.title('Voltage Profile')
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()
            
    def plot_branch_flows(self, save_path: Optional[str] = None):
        """
        Plot the branch flow magnitudes.
        
        Args:
            save_path: Optional path to save the plot
        """
        # Get branch flows
        flows = {}
        for (i, j) in self.branches:
            p_flow = self.values['Pij'][(i, j)]
            q_flow = self.values['Qij'][(i, j)]
            s_flow = np.sqrt(p_flow**2 + q_flow**2)
            flows[f"{i}-{j}"] = s_flow
            
        # Create DataFrame for plotting
        df = pd.DataFrame({
            'Branch': list(flows.keys()),
            'Flow (MVA)': list(flows.values())
        })
        
        # Plot
        plt.figure(figsize=(12, 6))
        sns.barplot(x='Branch', y='Flow (MVA)', data=df)
        plt.title('Branch Flow Magnitudes')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()
            
    def plot_generation_dispatch(self, save_path: Optional[str] = None):
        """
        Plot the generation dispatch.
        
        Args:
            save_path: Optional path to save the plot
        """
        # Create DataFrame for plotting
        df = pd.DataFrame({
            'Generator': list(self.values['Pg'].keys()),
            'Real Power (MW)': list(self.values['Pg'].values()),
            'Reactive Power (MVAr)': list(self.values['Qg'].values())
        })
        
        # Plot
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        sns.barplot(x='Generator', y='Real Power (MW)', data=df, ax=axes[0])
        axes[0].set_title('Real Power Generation')
        axes[0].tick_params(axis='x', rotation=45)
        
        sns.barplot(x='Generator', y='Reactive Power (MVAr)', data=df, ax=axes[1])
        axes[1].set_title('Reactive Power Generation')
        axes[1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()
            
    def plot_network_topology(self, save_path: Optional[str] = None):
        """
        Plot the network topology with branch flows.
        
        Args:
            save_path: Optional path to save the plot
        """
        # Create network graph
        G = nx.Graph()
        
        # Add nodes (buses)
        for bus in self.buses:
            G.add_node(bus, 
                      voltage=self.values['V'][bus],
                      is_generator=bus in self.generators)
        
        # Add edges (branches)
        for (i, j) in self.branches:
            p_flow = self.values['Pij'][(i, j)]
            q_flow = self.values['Qij'][(i, j)]
            s_flow = np.sqrt(p_flow**2 + q_flow**2)
            G.add_edge(i, j, flow=s_flow)
        
        # Plot
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G)
        
        # Draw nodes
        node_colors = ['red' if G.nodes[n]['is_generator'] else 'blue' 
                      for n in G.nodes()]
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=500)
        
        # Draw edges with flow width
        edge_widths = [G.edges[e]['flow']/10 for e in G.edges()]
        nx.draw_networkx_edges(G, pos, width=edge_widths)
        
        # Add labels
        nx.draw_networkx_labels(G, pos)
        edge_labels = {(i, j): f"{G.edges[(i, j)]['flow']:.1f}" 
                      for (i, j) in G.edges()}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
        
        plt.title('Network Topology with Branch Flows')
        
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()
            
    def plot_constraint_violations(self, save_path: Optional[str] = None):
        """Plot constraint violations for the solved model.
        
        Args:
            save_path (str): Path to save the plot
        """
        violations = []
        
        # Check voltage magnitude violations
        for b in self.buses:
            v = self.values['V'][b]
            v_min = self.values['V_min'][b]
            v_max = self.values['V_max'][b]
            if v < v_min - 1e-3:
                violations.append(f"Bus {b} voltage {v:.3f} below min {v_min:.3f}")
            elif v > v_max + 1e-3:
                violations.append(f"Bus {b} voltage {v:.3f} above max {v_max:.3f}")
                
        # Check generator real power violations
        for g in self.generators:
            pg = self.values['Pg'][g]
            pg_min = self.values['Pg_min'][g]
            pg_max = self.values['Pg_max'][g]
            if pg < pg_min - 1e-3:
                violations.append(f"Generator {g} P {pg:.3f} below min {pg_min:.3f}")
            elif pg > pg_max + 1e-3:
                violations.append(f"Generator {g} P {pg:.3f} above max {pg_max:.3f}")
                
        # Check generator reactive power violations
        for g in self.generators:
            qg = self.values['Qg'][g]
            qg_min = self.values['Qg_min'][g]
            qg_max = self.values['Qg_max'][g]
            if qg < qg_min - 1e-3:
                violations.append(f"Generator {g} Q {qg:.3f} below min {qg_min:.3f}")
            elif qg > qg_max + 1e-3:
                violations.append(f"Generator {g} Q {qg:.3f} above max {qg_max:.3f}")
                
        # Check branch flow violations
        for (i, j) in self.branches:
            p_flow = self.values['Pij'][(i, j)]
            q_flow = self.values['Qij'][(i, j)]
            sij = np.sqrt(p_flow**2 + q_flow**2)
            sij_max = self.values['Sij_max'][(i, j)]
            if sij > sij_max + 1e-3:
                violations.append(f"Branch {i}-{j} flow {sij:.3f} above limit {sij_max:.3f}")
                
        if not violations:
            print("No constraint violations found")
            return
            
        # Create a figure to display violations
        plt.figure(figsize=(15, 10))
        plt.text(0.1, 0.9, '\n'.join(violations), fontsize=12, family='monospace')
        plt.axis('off')
        plt.title('Constraint Violations', pad=20)
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            plt.close()
            
    def create_dashboard(self, save_dir: str):
        """
        Create a comprehensive dashboard of visualizations.
        
        Args:
            save_dir: Directory to save the visualization files
        """
        self.plot_voltage_profile(f"{save_dir}/voltage_profile.png")
        self.plot_branch_flows(f"{save_dir}/branch_flows.png")
        self.plot_generation_dispatch(f"{save_dir}/generation_dispatch.png")
        self.plot_network_topology(f"{save_dir}/network_topology.png")
        self.plot_constraint_violations(f"{save_dir}/constraint_violations.png") 