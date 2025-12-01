# Arbitrage Engine

This project is an autonomous cross-venue funding rate arbitrage engine connecting to Hyperliquid, dYdX, GMX, Aster, and Lighter.

## Prerequisites

- Python 3.7+
- pip

## Installation

1. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

To run the arbitrage engine, you need to execute the `arbitrage_engine/main.py` script. Ensure that the project root is in your `PYTHONPATH`.

### Option 1: Using the helper script (Recommended)

   ```bash
   chmod +x run.sh
   ./run.sh
   ```

### Option 2: Manual execution

   ```bash
   export PYTHONPATH=$PYTHONPATH:.
   python3 arbitrage_engine/main.py
   ```

## Structure

- `arbitrage_engine/adapters/`: Contains exchange-specific adapters (Hyperliquid, dYdX, GMX*, Aster, Lighter).
- `arbitrage_engine/core/`: Contains core interfaces and normalization logic.
- `arbitrage_engine/main.py`: The main entry point that aggregates data and finds opportunities.

\* *Note: GMX adapter is currently a placeholder pending public API verification.*
