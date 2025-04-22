# Power Grid Dataset Generator

A Python-based pipeline for generating synthetic power grid datasets suitable for optimization testing and machine learning model training.

## Features

- Automated generation of diverse power grid scenarios
- Support for load profile variations and N-1 contingencies
- Power flow and DC OPF simulations using pandapower
- Structured data output in CSV/Parquet formats
- ML-ready dataset formatting

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

## Installation

1. Clone this repository
2. Create a virtual environment:
```bash
cd power-grid-dataset-generator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```