import pandapower as pp
import numpy as np
import logging
from typing import Dict, List, Any
from tqdm import tqdm

logger = logging.getLogger(__name__)

class ScenarioGenerator:
    """Class for generating different power grid operating scenarios."""
    
    def __init__(self):
        """Initialize the scenario generator."""
        self.scenario_types = {
            'load_variation': self._generate_load_variation,
            'n1_contingency': self._generate_n1_contingency,
            'generation_variation': self._generate_generation_variation
        }
    
    def generate_scenarios(self, grid_data: Dict[str, Any], 
                          num_scenarios: int = 100,
                          scenario_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        Generate multiple scenarios for the given grid.
        
        Args:
            grid_data: Dictionary containing the grid model and metadata
            num_scenarios: Number of scenarios to generate
            scenario_types: List of scenario types to generate (default: all)
            
        Returns:
            List of scenario dictionaries
        """
        if scenario_types is None:
            scenario_types = list(self.scenario_types.keys())
            
        scenarios = []
        net = grid_data['net']
        
        logger.info(f"Generating {num_scenarios} scenarios...")
        for _ in tqdm(range(num_scenarios)):
            # Randomly select a scenario type
            scenario_type = np.random.choice(scenario_types)
            
            # Generate the scenario
            scenario = self.scenario_types[scenario_type](net)
            scenario['scenario_type'] = scenario_type
            scenario['grid_metadata'] = grid_data['metadata']
            
            # Run power flow
            try:
                pp.runpp(scenario['net'])
                scenario['converged'] = True
            except Exception as e:
                logger.warning(f"Power flow did not converge: {str(e)}")
                scenario['converged'] = False
            
            scenarios.append(scenario)
        
        return scenarios
    
    def _generate_load_variation(self, net: pp.pandapowerNet) -> Dict[str, Any]:
        """Generate a scenario with varying load profiles."""
        scenario_net = net.deepcopy()
        
        # Randomly vary load values between 50% and 150% of base values
        for idx in scenario_net.load.index:
            base_p = scenario_net.load.at[idx, 'p_mw']
            base_q = scenario_net.load.at[idx, 'q_mvar']
            
            # Generate random variation factors
            p_factor = np.random.uniform(0.5, 1.5)
            q_factor = np.random.uniform(0.5, 1.5)
            
            # Apply variations
            scenario_net.load.at[idx, 'p_mw'] = base_p * p_factor
            scenario_net.load.at[idx, 'q_mvar'] = base_q * q_factor
        
        return {
            'net': scenario_net,
            'variation_type': 'load',
            'variation_params': {
                'p_factor_range': (0.5, 1.5),
                'q_factor_range': (0.5, 1.5)
            }
        }
    
    def _generate_n1_contingency(self, net: pp.pandapowerNet) -> Dict[str, Any]:
        """Generate a scenario with N-1 contingency."""
        scenario_net = net.deepcopy()
        
        # Randomly select a line to remove
        line_idx = np.random.choice(scenario_net.line.index)
        removed_line = scenario_net.line.loc[line_idx]
        
        # Remove the selected line
        scenario_net.line.drop(line_idx, inplace=True)
        
        return {
            'net': scenario_net,
            'variation_type': 'n1_contingency',
            'variation_params': {
                'removed_line': {
                    'from_bus': removed_line['from_bus'],
                    'to_bus': removed_line['to_bus'],
                    'length_km': removed_line['length_km']
                }
            }
        }
    
    def _generate_generation_variation(self, net: pp.pandapowerNet) -> Dict[str, Any]:
        """Generate a scenario with varying generation profiles."""
        scenario_net = net.deepcopy()
        
        # Randomly vary generation values between 50% and 150% of base values
        for idx in scenario_net.gen.index:
            base_p = scenario_net.gen.at[idx, 'p_mw']
            
            # Generate random variation factor
            p_factor = np.random.uniform(0.5, 1.5)
            
            # Apply variation
            scenario_net.gen.at[idx, 'p_mw'] = base_p * p_factor
        
        return {
            'net': scenario_net,
            'variation_type': 'generation',
            'variation_params': {
                'p_factor_range': (0.5, 1.5)
            }
        } 