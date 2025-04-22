import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import networkx as nx

class OPFVisualizer:
    def __init__(self, case_data, results):
        """
        Initialize visualizer with case data and OPF results
        
        Args:
            case_data (dict): Dictionary containing bus, branch, and generator data
            results (dict): Dictionary containing OPF solution results
        """
        self.case_data = case_data
        self.results = results
        
    def plot_voltage_profile(self, save_path=None):
        """Plot voltage magnitude profile across all buses"""
        plt.figure(figsize=(12, 6))
        buses = self.case_data['buses'].index
        voltages = [self.results['V'][b] for b in buses]
        
        plt.bar(buses, voltages)
        plt.axhline(y=1.0, color='r', linestyle='--', label='Nominal Voltage')
        plt.axhline(y=1.1, color='g', linestyle='--', label='Upper Limit')
        plt.axhline(y=0.9, color='g', linestyle='--', label='Lower Limit')
        
        plt.xlabel('Bus Number')
        plt.ylabel('Voltage Magnitude (p.u.)')
        plt.title('Voltage Profile')
        plt.legend()
        plt.grid(True)
        
        if save_path:
            plt.savefig(save_path)
        plt.show()
        
    def plot_power_flow(self, save_path=None):
        """Plot power flow on branches"""
        plt.figure(figsize=(12, 8))
        G = nx.Graph()
        
        # Add nodes
        for bus in self.case_data['buses'].index:
            G.add_node(bus)
            
        # Add edges with power flow values
        for idx, branch in self.case_data['branches'].iterrows():
            from_bus = branch['from_bus']
            to_bus = branch['to_bus']
            flow = self.results['branch_flows'][idx]
            G.add_edge(from_bus, to_bus, weight=flow)
            
        # Draw the network
        pos = nx.spring_layout(G)
        nx.draw_networkx_nodes(G, pos, node_size=700)
        nx.draw_networkx_edges(G, pos, width=2)
        nx.draw_networkx_labels(G, pos)
        
        # Add edge labels with power flow values
        edge_labels = {(u, v): f"{d['weight']:.2f}" for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
        
        plt.title('Power Flow Distribution')
        
        if save_path:
            plt.savefig(save_path)
        plt.show()
        
    def plot_generator_output(self, save_path=None):
        """Plot generator real and reactive power output"""
        plt.figure(figsize=(12, 6))
        
        generators = self.case_data['generators'].index
        Pg = [self.results['Pg'][g] for g in generators]
        Qg = [self.results['Qg'][g] for g in generators]
        
        x = np.arange(len(generators))
        width = 0.35
        
        plt.bar(x - width/2, Pg, width, label='Real Power (MW)')
        plt.bar(x + width/2, Qg, width, label='Reactive Power (MVAr)')
        
        plt.xlabel('Generator')
        plt.ylabel('Power Output')
        plt.title('Generator Output')
        plt.xticks(x, generators)
        plt.legend()
        plt.grid(True)
        
        if save_path:
            plt.savefig(save_path)
        plt.show()
        
    def plot_constraint_violations(self, save_path=None):
        """Plot constraint violations if any"""
        violations = self._get_constraint_violations()
        
        if not violations:
            print("No constraint violations found")
            return
            
        plt.figure(figsize=(12, 6))
        
        # Plot voltage violations
        if 'voltage' in violations:
            plt.subplot(1, 2, 1)
            buses = violations['voltage'].index
            values = violations['voltage'].values
            plt.bar(buses, values)
            plt.title('Voltage Violations')
            plt.xlabel('Bus')
            plt.ylabel('Violation (p.u.)')
            
        # Plot branch flow violations
        if 'branch_flow' in violations:
            plt.subplot(1, 2, 2)
            branches = violations['branch_flow'].index
            values = violations['branch_flow'].values
            plt.bar(branches, values)
            plt.title('Branch Flow Violations')
            plt.xlabel('Branch')
            plt.ylabel('Violation (MVA)')
            
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
        plt.show()
        
    def _get_constraint_violations(self):
        """Calculate constraint violations"""
        violations = {}
        
        # Check voltage violations
        voltage_violations = {}
        for bus in self.case_data['buses'].index:
            V = self.results['V'][bus]
            if V < 0.9 or V > 1.1:
                voltage_violations[bus] = max(abs(V - 1.1), abs(V - 0.9))
        if voltage_violations:
            violations['voltage'] = pd.Series(voltage_violations)
            
        # Check branch flow violations
        branch_violations = {}
        for idx, branch in self.case_data['branches'].iterrows():
            flow = self.results['branch_flows'][idx]
            limit = branch['rate_a']
            if flow > limit:
                branch_violations[idx] = flow - limit
        if branch_violations:
            violations['branch_flow'] = pd.Series(branch_violations)
            
        return violations 