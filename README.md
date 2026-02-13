# ResQEnergy NPRO Building Data Package

This package allows easy simulations of different weather scenarios using an existing NPRO project.
For each building set up in a NPRO project, weather data read from the scenarios folder is adapted and resulting building energies are stored locally.

## Installation

Set up environment: `uv venv .venv`
Activate env: `source .venv/bin/activate`
Install packages: `uv sync`

## Scenarios

Weather data must be provided as semicolon-separated CSV-files containing timeseries.
Possible columns are _air_temperature_mean_, _wind_speed_, _radiation_downwelling_, _radiation_direct_ and _infrared_.
If one of these columns is not set, NPRO uses its default timeseries.

## Usage

All commands are available running the main script.
See available commands: `uv run main.py -h`

To log in to NPRO some environment variables have to be set.
This can be done using an `.env` file and setting vars `NPRO_EMAIL`, `NPRO_PASSWORD` and `NPRO_PROJECT`.
Available projects can be seen using `uv run main.py list`.
Example `.env` file:
```dotenv
DEBUG=False

NPRO_EMAIL=<nonname@test.de>
NPRO_PASSWORD=<password>
NPRO_PROJECT=<projectName>
```

To run all scenarios with all related buildings run `uv run main.py run all`.
If you want to run a specific scenario you can call `uv run main.py run <scenario_name>`.
Results will be stored in folder _results_ in a folder named like the scenario. 