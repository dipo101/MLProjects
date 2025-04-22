import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Any
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

class DataFormatter:
    """Class for formatting and saving power grid scenarios."""
    
    def save_scenarios(self, scenarios: List[Dict[str, Any]], output_dir: Path) -> None:
        """
        Save the generated scenarios to disk.
        
        Args:
            scenarios: List of scenario dictionaries
            output_dir: Directory to save the scenarios
        """
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert scenarios to DataFrames
        bus_data = self._extract_bus_data(scenarios)
        line_data = self._extract_line_data(scenarios)
        load_data = self._extract_load_data(scenarios)
        gen_data = self._extract_gen_data(scenarios)
        scenario_metadata = self._extract_scenario_metadata(scenarios)
        
        # Save as Parquet files
        logger.info("Saving scenario data...")
        self._save_parquet(bus_data, output_dir / "bus_data.parquet")
        self._save_parquet(line_data, output_dir / "line_data.parquet")
        self._save_parquet(load_data, output_dir / "load_data.parquet")
        self._save_parquet(gen_data, output_dir / "gen_data.parquet")
        self._save_parquet(scenario_metadata, output_dir / "scenario_metadata.parquet")
        
        # Also save as CSV for easy inspection
        logger.info("Saving CSV files for inspection...")
        bus_data.to_csv(output_dir / "bus_data.csv", index=False)
        line_data.to_csv(output_dir / "line_data.csv", index=False)
        load_data.to_csv(output_dir / "load_data.csv", index=False)
        gen_data.to_csv(output_dir / "gen_data.csv", index=False)
        scenario_metadata.to_csv(output_dir / "scenario_metadata.csv", index=False)
    
    def _extract_bus_data(self, scenarios: List[Dict[str, Any]]) -> pd.DataFrame:
        """Extract bus data from scenarios."""
        bus_data = []
        
        for i, scenario in enumerate(scenarios):
            if not scenario['converged']:
                continue
                
            net = scenario['net']
            for idx, bus in net.bus.iterrows():
                bus_data.append({
                    'scenario_id': i,
                    'bus_id': idx,
                    'name': bus['name'],
                    'vn_kv': bus['vn_kv'],
                    'vm_pu': net.res_bus.at[idx, 'vm_pu'],
                    'va_degree': net.res_bus.at[idx, 'va_degree']
                })
        
        return pd.DataFrame(bus_data)
    
    def _extract_line_data(self, scenarios: List[Dict[str, Any]]) -> pd.DataFrame:
        """Extract line data from scenarios."""
        line_data = []
        
        for i, scenario in enumerate(scenarios):
            if not scenario['converged']:
                continue
                
            net = scenario['net']
            for idx, line in net.line.iterrows():
                line_data.append({
                    'scenario_id': i,
                    'line_id': idx,
                    'from_bus': line['from_bus'],
                    'to_bus': line['to_bus'],
                    'length_km': line['length_km'],
                    'p_from_mw': net.res_line.at[idx, 'p_from_mw'],
                    'q_from_mvar': net.res_line.at[idx, 'q_from_mvar'],
                    'p_to_mw': net.res_line.at[idx, 'p_to_mw'],
                    'q_to_mvar': net.res_line.at[idx, 'q_to_mvar'],
                    'loading_percent': net.res_line.at[idx, 'loading_percent']
                })
        
        return pd.DataFrame(line_data)
    
    def _extract_load_data(self, scenarios: List[Dict[str, Any]]) -> pd.DataFrame:
        """Extract load data from scenarios."""
        load_data = []
        
        for i, scenario in enumerate(scenarios):
            if not scenario['converged']:
                continue
                
            net = scenario['net']
            for idx, load in net.load.iterrows():
                load_data.append({
                    'scenario_id': i,
                    'load_id': idx,
                    'bus': load['bus'],
                    'p_mw': load['p_mw'],
                    'q_mvar': load['q_mvar'],
                    'p_mw_set': load['p_mw'],
                    'q_mvar_set': load['q_mvar']
                })
        
        return pd.DataFrame(load_data)
    
    def _extract_gen_data(self, scenarios: List[Dict[str, Any]]) -> pd.DataFrame:
        """Extract generator data from scenarios."""
        gen_data = []
        
        for i, scenario in enumerate(scenarios):
            if not scenario['converged']:
                continue
                
            net = scenario['net']
            for idx, gen in net.gen.iterrows():
                gen_data.append({
                    'scenario_id': i,
                    'gen_id': idx,
                    'bus': gen['bus'],
                    'p_mw': gen['p_mw'],
                    'vm_pu': gen['vm_pu'],
                    'p_mw_set': gen['p_mw'],
                    'vm_pu_set': gen['vm_pu']
                })
        
        return pd.DataFrame(gen_data)
    
    def _extract_scenario_metadata(self, scenarios: List[Dict[str, Any]]) -> pd.DataFrame:
        """Extract scenario metadata."""
        metadata = []
        
        for i, scenario in enumerate(scenarios):
            metadata.append({
                'scenario_id': i,
                'scenario_type': scenario['scenario_type'],
                'converged': scenario['converged'],
                'variation_type': scenario['variation_type'],
                'variation_params': str(scenario['variation_params']),
                'grid_type': scenario['grid_metadata']['grid_type'],
                'num_buses': scenario['grid_metadata']['num_buses'],
                'num_lines': scenario['grid_metadata']['num_lines'],
                'num_generators': scenario['grid_metadata']['num_generators'],
                'num_loads': scenario['grid_metadata']['num_loads']
            })
        
        return pd.DataFrame(metadata)
    
    def _save_parquet(self, df: pd.DataFrame, filepath: Path) -> None:
        """Save DataFrame as Parquet file."""
        table = pa.Table.from_pandas(df)
        pq.write_table(table, filepath) 