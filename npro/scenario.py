"""Module to load and update scenario data."""

from __future__ import annotations

import copy
import json
from functools import reduce
from typing import Any, Iterator

import pandas as pd
import yaml

from npro import api, infrared, settings

MAPPINGS = {
    "air_temperature_mean": "airTemp",
    "wind_speed": "windSpeed",
    "radiation_downwelling": "ghi",
    "radiation_direct": "dni",
    "infrared": "ir",
}

BUILDING_ENERGIE_KEYS = (
    ("dhwProfile",),
    ("emobProfile",),
    ("elecDem", "import", "profile"),
    ("elecBes", "import", "profile"),
    ("cool", "import", "profile"),
    ("distrCool", "import", "profile"),
    ("heat", "import", "profile"),
    ("spaceCoolProfile",),
    ("processCoolProfile",),
    ("spaceHeatProfile",),
    ("plugLoadsProfile",),
)

BUILDING_TRIGGERS = {
    "addrCountry": "country",
    "addrCity": "city",
    "buildingType": "buildingType",
    "buildingSubtype": "buildingSubtype",
    "floorArea": "floorArea",
}


def get_list_of_scenarios() -> Iterator[str]:
    """Get list of scenarios."""
    for scenario_file in settings.SCENARIOS_DIR.iterdir():
        if scenario_file.suffix == ".yaml":
            yield scenario_file.stem


def load_scenario(scenario_name: str) -> dict:
    """Load scenario from scenarios folder."""
    filepath = settings.SCENARIOS_DIR / f"{scenario_name}.yaml"
    if not filepath.exists():
        raise FileNotFoundError(
            f"Could not find scenario '{scenario_name}.yaml' in scenario folder."
        )
    with filepath.open("r") as f:
        scenario_data = yaml.safe_load(f)
    settings.logger.info(f"Loaded scenario '{scenario_name}'.")
    return scenario_data


def load_weather_data(name: str) -> dict[str, list[float]]:
    """Load weather data from scenario file."""
    filename = f"{name}.csv"
    data = pd.read_csv(settings.WEATHER_DIR / filename, sep=";")
    data["infrared"] = infrared.calculate_longwave_radiation(data)
    data = data.drop(
        [column for column in data.columns if column not in MAPPINGS], axis=1
    )
    data = data.rename(columns=MAPPINGS)
    settings.logger.info(f"Loaded weather data '{name}'.")
    return data.to_dict(orient="list")


def load_building(building_name: str) -> dict:
    """Load building from buildings folder."""
    filename = f"{building_name}.json"
    if not (settings.BUILDINGS_DIR / filename).exists():
        raise FileNotFoundError(
            f"Building '{building_name}' not found in {settings.BUILDINGS_DIR}."
        )
    with (settings.BUILDINGS_DIR / filename).open("r") as f:
        building_data = json.load(f)
    settings.logger.info(f"Loaded building data for building '{building_name}'.")
    return building_data


def adapt_building(building_data: dict, building_update_data: dict) -> dict:
    """
    Update building data.

    Updating building data might trigger recalculation of default values.
    Currently, if this happens, all default values will override existing values.
    """
    current_building_data = copy.deepcopy(building_data)
    current_building_data.update(building_update_data)
    if any(key in BUILDING_TRIGGERS for key in building_update_data):
        building_type_data = {
            mapped_key: current_building_data[key] for key, mapped_key in BUILDING_TRIGGERS.items()
        }
        default_values = api.get_default_building_data(building_type_data)
        current_building_data.update(default_values)
    return current_building_data


def adapt_building_list_by_scenario(
    building_list: list[dict], scenario_buildings: dict[str, dict[str, Any]]
) -> list[dict]:
    """
    Adapt buildings in building list based on scenario buildings.
    """
    new_building_list = []
    for new_building_name, scenario_building_data in scenario_buildings.items():
        scenario_building_data["buildingName"] = new_building_name
        if "based_on" not in scenario_building_data:
            raise KeyError(
                f"Key 'based_on' not found in scenario building '{new_building_name}'."
            )
        based_on = scenario_building_data.pop("based_on")
        building_data = get_building_by_name(
            building_list, based_on
        )
        updated_building_data = adapt_building(building_data, scenario_building_data)
        new_building_list.append(updated_building_data)
    settings.logger.info("Adapted building list by scenario buildings.")
    return new_building_list


def update_weather_data(
    scenario_data: dict, weather_data: dict[str, list[float]]
) -> dict:
    """Update scenario data with weather data."""
    for key, timeseries in weather_data.items():
        scenario_data["proj_json"][key] = timeseries

    # Remove weather timeseries which are not mapped (default is used)
    missing_weather_keys = set(MAPPINGS.values()) - set(weather_data.keys())
    for key in missing_weather_keys:
        scenario_data["proj_json"][key] = []
    settings.logger.info("Updated weather data in project.")
    return scenario_data


def calculate_building_for_scenario(
    scenario_name: str, building: dict | None = None
) -> None:
    """Run a simulation with given scenario."""
    session = api.setup_session()
    api.login(session)
    project_data = api.load_project(session)
    scenario = load_scenario(scenario_name)
    weather_data = load_weather_data(scenario["weather"])
    project_data = update_weather_data(project_data, weather_data)
    api.run_simulation(session, project_data)

    # Set up buildings
    if building is None:
        buildings = api.get_list_of_buildings(project_data)
    else:
        buildings = [building]

    # Adapt buildings from scenario
    if "buildings" in scenario:
        buildings = adapt_building_list_by_scenario(buildings, scenario["buildings"])

    # Empty building list, as this is unneeded overhead
    project_data["proj_json"]["buildingList"] = {}

    # Run each building
    for building_data in buildings:
        result = api.calc_building(session, building_data, project_data)
        store_building_result_as_json(scenario_name, result)
        store_building_result_as_csv(scenario_name, result)


def store_building_result_as_json(scenario_name: str, building_data: dict) -> None:
    """Store building result as JSON in scenario folder of results folder."""
    filename = f"{building_data['buildingName']}.json"
    target = settings.RESULTS_DIR / scenario_name
    target.mkdir(exist_ok=True, parents=True)
    with (target / filename).open("w") as f:
        json.dump(building_data, f, indent=2)
    settings.logger.info(f"Stored building data as {filename} in {target}.")


def store_building_result_as_csv(scenario_name: str, building_data: dict) -> None:
    """Store building result as CSV in scenario folder of results folder."""
    filename = f"{building_data['buildingName']}.csv"
    target = settings.RESULTS_DIR / scenario_name
    target.mkdir(exist_ok=True, parents=True)
    df = pd.DataFrame(
        {
            keys[0]: reduce(lambda current, key: current[key], keys, building_data)
            for keys in BUILDING_ENERGIE_KEYS
        }
    )
    df.to_csv(target / filename, index=False)
    settings.logger.info(f"Stored building data as {filename} in {target}.")


def get_building_by_name(building_list: list, building_name: str) -> dict:
    """Return configured NPRO building by name."""
    for building_data in building_list:
        if building_data["buildingName"] == building_name:
            if settings.DEBUG:
                settings.save_debug_data(building_data, "building")
            return building_data
    raise KeyError(f"Building with name '{building_name}' not found.")
