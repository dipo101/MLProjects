# OPF Solver Comparison and Visualization

This project implements and compares Optimal Power Flow (OPF) solutions on standard IEEE test grids, with a focus on visualization of grid operating states and operational constraint violations.

## Features

- AC OPF problem formulation using Pyomo
- Interface with open-source solvers (IPOPT)
- Analysis of thermal and voltage constraint adherence
- Visualization of grid states and constraint violations
- Support for standard IEEE test cases

## Project Structure

```
opf-solvers/
├── src/
│   ├── opf/              # OPF problem formulation
│   ├── solvers/          # Solver interfaces
│   ├── visualization/    # Visualization tools
│   └── test_cases/       # IEEE test case implementations
├── tests/               # Unit tests
├── examples/            # Example scripts
└── data/               # Test case data
```

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

See the examples directory for usage examples with different IEEE test cases.

## License

MIT License 