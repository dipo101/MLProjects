import pandapower as pp
import numpy as np
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class GridGenerator:
    """Class for generating base power grid models."""
    
    def __init__(self):
        """Initialize the grid generator."""
        self.available_grids = {
            'case9': self._create_case9,
            'case14': self._create_case14,
            'case30': self._create_case30,
            # Add more standard test cases as needed
        }
    
    def create_base_grid(self, grid_type: str = 'case9') -> Dict[str, Any]:
        """
        Create a base power grid model.
        
        Args:
            grid_type: Type of grid to create (default: 'case9')
            
        Returns:
            Dictionary containing the grid model and metadata
        """
        if grid_type not in self.available_grids:
            raise ValueError(f"Unknown grid type: {grid_type}")
            
        logger.info(f"Creating {grid_type} grid...")
        net = self.available_grids[grid_type]()
        
        return {
            'grid_type': grid_type,
            'net': net,
            'metadata': self._generate_metadata(net, grid_type)
        }
    
    def _create_case9(self) -> pp.pandapowerNet:
        """Create the IEEE 9-bus test case using pandapower's built-in case."""
        # Create the case9 network using pandapower's built-in function
        net = pp.networks.case9()
        
        # Modify the network slightly to match our needs
        # Update generator settings
        net.gen.loc[0, "p_mw"] = 200
        net.gen.loc[1, "p_mw"] = 300
        net.gen.loc[0, "min_q_mvar"] = -150
        net.gen.loc[0, "max_q_mvar"] = 150
        net.gen.loc[1, "min_q_mvar"] = -150
        net.gen.loc[1, "max_q_mvar"] = 150
        
        # Update load settings to match our desired values
        net.load.loc[0, "p_mw"] = 100
        net.load.loc[0, "q_mvar"] = 40
        net.load.loc[1, "p_mw"] = 90
        net.load.loc[1, "q_mvar"] = 30
        net.load.loc[2, "p_mw"] = 100
        net.load.loc[2, "q_mvar"] = 35
        
        # The built-in case9 comes with proper line parameters
        return net
    
    def _create_case14(self) -> pp.pandapowerNet:
        """Create the IEEE 14-bus test case."""
        # Implementation for IEEE 14-bus system
        raise NotImplementedError("IEEE 14-bus system not yet implemented")
    
    def _create_case30(self) -> pp.pandapowerNet:
        """Create the IEEE 30-bus test case."""
        # Implementation for IEEE 30-bus system
        raise NotImplementedError("IEEE 30-bus system not yet implemented")
    
    def _generate_metadata(self, net: pp.pandapowerNet, grid_type: str) -> Dict[str, Any]:
        """Generate metadata for the grid model."""
        return {
            'grid_type': grid_type,
            'num_buses': len(net.bus),
            'num_lines': len(net.line),
            'num_generators': len(net.gen),
            'num_loads': len(net.load),
            'base_voltage': net.bus.vn_kv.mean(),
            'total_load': net.load.p_mw.sum(),
            'total_generation': net.gen.p_mw.sum()
        } 