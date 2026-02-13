"""Module to load and update scenario data."""
from __future__ import annotations

import json
from typing import Iterator

import settings
import api
import pandas as pd

MAPPINGS = {
    "air_temperature_mean": "airTemp",
    "wind_speed": "windSpeed",
    "radiation_downwelling": "ghi",
    "radiation_direct": "dni",
    "infrared": "ir"
}

def get_list_of_scenarios() -> Iterator[str]:
    """Get list of scenarios."""
    for scenario_file in settings.SCENARIOS_DIR.iterdir():
        if scenario_file.suffix == ".csv":
            yield scenario_file.stem

def load_scenario_weather_data(scenario: str) -> dict[str, list[float]]:
    """Load weather data from scenario file."""
    filename = f"{scenario}.csv"
    data = pd.read_csv(settings.SCENARIOS_DIR / filename, sep=";")
    data = data.drop([column for column in data.columns if column not in MAPPINGS], axis=1)
    data = data.rename(columns=MAPPINGS)
    return data.to_dict(orient="list")


def update_weather_data(scenario_data: dict, weather_data: dict[str, list[float]]) -> dict:
    """Update scenario data with weather data."""
    for key, timeseries in weather_data.items():
        scenario_data["proj_json"][key] = timeseries

    # Remove weather timeseries which are not mapped (default is used)
    missing_weather_keys = set(MAPPINGS.values()) - set(weather_data.keys())
    for key in missing_weather_keys:
        scenario_data["proj_json"][key] = []
    return scenario_data


def store_building_result(scenario_name: str, building_data: dict) -> None:
    """Store building result in scenario folder of results folder."""
    filename = f"{building_data['buildingName']}.json"
    target = settings.RESULTS_DIR / scenario_name
    target.mkdir(exist_ok=True)
    with (target / filename).open("w") as f:
        json.dump(building_data, f, indent=2)
    settings.logger.info(f"Stored building data as {filename} in {target}.")


def calculate_building_for_scenario(scenario_name: str, building: dict | None = None) -> None:
    """Run a simulation with given scenario."""
    session = api.setup_session()
    api.login(session)
    project_data = api.load_scenario(session, settings.NPRO_PROJECT)
    weather_data = load_scenario_weather_data(scenario_name)
    project_data = update_weather_data(project_data, weather_data)
    if building is None:
        buildings = api.get_list_of_buildings(project_data)
    else:
        buildings = [building]
    for building_data in buildings:
        result = api.calc_building(session, building_data, project_data)
        store_building_result(scenario_name, result)




if __name__ == "__main__":
    print(list(get_list_of_scenarios()))
    # d = load_scenario_weather_data("try_mean_rcp85.p3")
    # s = update_scenario_weather_data({"proj_json": {"ir": 5}}, d)