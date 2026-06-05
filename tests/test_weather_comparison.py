"""Test building calculation with two different weather files."""

import copy
import pathlib

import pandas as pd

from npro import api, scenario, settings

BUILDING_NAME = "Einfamilienhaus (ab 2002) | decentral"
WEATHER_FILES = ["try_extr1_rcp85.p3.txt", "try_extr2_rcp85.p3.txt", "try_extr3_rcp85.p3.txt"]
TEST_DATA_DIR = pathlib.Path(__file__).parent / "test_data"

BUILDING_UPDATE_DATA = {
    "floorArea": 1000,
    "shOption": "heatLoad",
    "peakDemHeatOption": "total",
    "calculate_cooling_demand": True
}


def _run_building_calc(
    session, project_data: dict, weather_file: str, result_dir: pathlib.Path, *, update_building: bool
) -> pathlib.Path:
    """Run single building calculation for given weather file, return CSV path.

    Args:
        session: Authenticated requests session.
        project_data: Loaded NPRO project data.
        weather_file: Weather filename (looked up in TEST_DATA_DIR).
        result_dir: Directory to write result CSV into.

    Returns:
        Path to the written CSV file.
    """
    project_copy = copy.deepcopy(project_data)
    weather_data = scenario.load_weather_data(weather_file)
    project_copy = scenario.update_weather_data(project_copy, weather_data)
    api.run_simulation(session, project_copy)

    building_list = api.get_list_of_buildings(project_copy)
    building_data = scenario.get_building_by_name(building_list, BUILDING_NAME)
    if update_building:
        building_data = scenario.adapt_building(building_data, BUILDING_UPDATE_DATA.copy(), weather_data)

    # Empty building list — unneeded overhead during single-building calc
    project_copy["proj_json"]["buildingList"] = {}

    result = api.calc_building(session, building_data, project_copy)

    scenario_name = weather_file.removesuffix(".txt").removesuffix(".csv")
    scenario.store_building_result_as_csv(scenario_name, result)

    return result_dir / scenario_name / f"{BUILDING_NAME}.csv"


def test_building_results_differ_by_weather(tmp_path, monkeypatch):
    """Building calculation with different weather files should produce different energy profiles.

    Currently the two test weather files produce equal column sums.
    Once weather-dependent code is updated, the assertion should be changed
    to verify the sums are NOT equal.
    """
    monkeypatch.setattr(settings, "WEATHER_DIR", TEST_DATA_DIR)
    monkeypatch.setattr(settings, "RESULT_DIR", tmp_path)

    session = api.setup_session()
    api.login(session)
    project_data = api.load_project(session)

    csv_paths = [
        _run_building_calc(session, project_data, wf, tmp_path, update_building=False)
        for wf in WEATHER_FILES
    ]

    dfs = [pd.read_csv(p) for p in csv_paths]
    sums = [df.sum() for df in dfs]

    for s in range(len(sums)):
        print(f"{WEATHER_FILES[s]}: {round(sums[s]['spaceHeatProfile'] / 1000)}")

    assert round(sums[0]['spaceHeatProfile']) != round(sums[1]['spaceHeatProfile'])
    assert round(sums[1]['spaceHeatProfile']) != round(sums[2]['spaceHeatProfile'])
    assert round(sums[2]['spaceHeatProfile']) != round(sums[0]['spaceHeatProfile'])

    assert round(sums[0]['spaceCoolProfile']) != round(sums[1]['spaceCoolProfile'])
    assert round(sums[1]['spaceCoolProfile']) != round(sums[2]['spaceCoolProfile'])
    assert round(sums[2]['spaceCoolProfile']) != round(sums[0]['spaceCoolProfile'])


def test_updated_building_results_differ_by_weather(tmp_path, monkeypatch):
    """Building calculation with different weather files should produce different energy profiles.

    Currently the two test weather files produce equal column sums.
    Once weather-dependent code is updated, the assertion should be changed
    to verify the sums are NOT equal.
    """
    monkeypatch.setattr(settings, "WEATHER_DIR", TEST_DATA_DIR)
    monkeypatch.setattr(settings, "RESULT_DIR", tmp_path)

    session = api.setup_session()
    api.login(session)
    project_data = api.load_project(session)

    csv_paths = [
        _run_building_calc(session, project_data, wf, tmp_path, update_building=True)
        for wf in WEATHER_FILES
    ]

    dfs = [pd.read_csv(p) for p in csv_paths]
    sums = [df.sum() for df in dfs]

    for s in range(len(sums)):
        print(f"{WEATHER_FILES[s]}: {round(sums[s]['spaceHeatProfile'] / 1000)}")

    assert round(sums[0]['spaceHeatProfile']) != round(sums[1]['spaceHeatProfile'])
    assert round(sums[1]['spaceHeatProfile']) != round(sums[2]['spaceHeatProfile'])
    assert round(sums[2]['spaceHeatProfile']) != round(sums[0]['spaceHeatProfile'])

    assert round(sums[0]['spaceCoolProfile']) != round(sums[1]['spaceCoolProfile'])
    assert round(sums[1]['spaceCoolProfile']) != round(sums[2]['spaceCoolProfile'])
    assert round(sums[2]['spaceCoolProfile']) != round(sums[0]['spaceCoolProfile'])
