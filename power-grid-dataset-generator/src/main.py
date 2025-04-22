import os
import sys
from pathlib import Path
import logging
from datetime import datetime

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))

from grid_generator import GridGenerator
from scenario_generator import ScenarioGenerator
from data_formatter import DataFormatter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'power_grid_dataset_generation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the dataset generation pipeline."""
    try:
        # Create output directory if it doesn't exist
        output_dir = Path("data/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        grid_gen = GridGenerator()
        scenario_gen = ScenarioGenerator()
        data_formatter = DataFormatter()
        
        # Generate base grid
        logger.info("Generating base grid...")
        base_grid = grid_gen.create_base_grid()
        
        # Generate scenarios
        logger.info("Generating scenarios...")
        scenarios = scenario_gen.generate_scenarios(base_grid)
        
        # Format and save data
        logger.info("Formatting and saving data...")
        data_formatter.save_scenarios(scenarios, output_dir)
        
        logger.info("Dataset generation completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in dataset generation: {str(e)}")
        raise

if __name__ == "__main__":
    main() 