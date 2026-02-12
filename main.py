import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()


def login(session):
    login_data = {
        "email": os.environ["EMAIL"],
        "password": os.environ["PASSWORD"],
        "remember_me": True,
    }
    login_response = session.post(
        "https://acad.npro.energy/api/login",
        headers={"Content-Type": "application/json"},
        json=login_data,
    )
    login_response.raise_for_status()


def get_list_of_projects(session: requests.Session) -> list[dict]:
    response = session.post(
        "https://acad.npro.energy/api/load_project_list",
        json={"sortModeProjects": "time"},
    )
    response.raise_for_status()
    data = response.json()
    if data["server_msg"] != "projectListLoaded":
        raise RuntimeError("Could not load project list.")
    return data["data"]["project_list"]


def load_scenario(session: requests.Session, projectStr: str):
    response = session.post(
        "https://acad.npro.energy/api/load_scenario", json={"projectStr": projectStr}
    )
    response.raise_for_status()
    data = response.json()
    if data["server_msg"] != "scenarioLoaded":
        raise RuntimeError("Could not load scenario.")
    return data["data"]


def calc_building(session: requests.Session, building_data: dict, scenario_data: dict) -> dict:
    data = {
        "newBuilding": building_data,
        "projectData": scenario_data["proj_json"],
    }
    response = session.post("https://acad.npro.energy/api/calc_building", json=data)
    response.raise_for_status()
    data = response.json()
    if data["response"] != "success":
        raise RuntimeError("Could not load building data.")
    return data["data"]


def run_simulation(session: requests.Session, scenario_data: dict):
    data = {
        "api_endpoint": "",
        "authenticated": True,
        "autoSaveProjects": 1,
        "calc_id": 53029542,
        "license": "academic",
        "BACKEND_VERSION": "4.0.0",
        "data": scenario_data["proj_json"],
    }
    response = session.post(
        "https://acad.npro.energy/api/calc_main", json=data
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    _session = requests.Session()
    login(_session)
    _projects = get_list_of_projects(_session)
    _scenario_data = load_scenario(_session, "2591-0-0")
    with open("scenario.json", "w") as f:
        json.dump(_scenario_data, f, indent=2)

    building = _scenario_data["proj_json"]["buildingList"]["0"]
    # Original results
    results_orig = calc_building(_session, building, _scenario_data)
    with open("results_orig.json", "w") as f:
        json.dump(results_orig, f, indent=2)

    # Change Temperature and rerun simulation
    _scenario_data["proj_json"]["airTemp"] = [2] * 8760
    run_simulation(_session, _scenario_data)

    results_changed = calc_building(_session, building, _scenario_data)
    with open("results_temp_changed.json", "w") as f:
        json.dump(results_changed, f, indent=2)

    diffs = {key: (value, results_changed[key]) for key, value in results_orig.items() if results_changed[key] != value}
    with open("diffs.json", "w") as f:
        json.dump(diffs, f, indent=2)
