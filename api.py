"""Module to run requests against NPRO API."""

import requests

import settings


def setup_session() -> requests.Session:
    """Set up session for NPRO API."""
    return requests.Session()


def login(session) -> None:
    """Login to NPRO API, session preserves login status."""
    login_data = {
        "email": settings.NPRO_EMAIL,
        "password": settings.NPRO_PASSWORD,
        "remember_me": True,
    }
    login_response = session.post(
        f"{settings.NPRO_API}/login",
        headers={"Content-Type": "application/json"},
        json=login_data,
    )
    login_response.raise_for_status()
    settings.logger.info("Successfully logged in.")


def get_list_of_projects(session: requests.Session) -> list[dict]:
    """Return list of configured NPRO projects."""
    response = session.post(
        f"{settings.NPRO_API}/load_project_list",
        json={"sortModeProjects": "time"},
    )
    response.raise_for_status()
    data = response.json()
    if data["server_msg"] != "projectListLoaded":
        raise RuntimeError("Could not load project list.")
    if settings.DEBUG:
        settings.save_debug_data(data["data"]["project_list"], "projects")
    return data["data"]["project_list"]


def get_list_of_buildings(scenario_data: dict) -> list[dict]:
    """Return list of configured NPRO buildings."""
    return list(scenario_data["proj_json"]["buildingList"].values())


def get_building_by_name(scenario_data: dict, building_name: str) -> dict:
    """Return configured NPRO building by name."""
    for building_id, building_data in scenario_data["proj_json"]["buildingList"].items():
        if building_data["buildingName"] == building_name:
            return building_data
    raise KeyError(f"Building with name '{building_name}' not found.")


def load_scenario(session: requests.Session, project: str = settings.NPRO_PROJECT) -> dict:
    """Load scenario data for given project."""
    if project is None:
        raise KeyError("Project not found. You can set it using env var NPRO_PROJECT.")
    response = session.post(
        f"{settings.NPRO_API}/load_scenario", json={"projectStr": project}
    )
    response.raise_for_status()
    data = response.json()
    if data["server_msg"] != "scenarioLoaded":
        raise RuntimeError("Could not load scenario.")
    if settings.DEBUG:
        settings.save_debug_data(data["data"], "scenario")
    settings.logger.info(f"Successfully loaded scenario '{settings.NPRO_PROJECT}'.")
    return data["data"]


def calc_building(session: requests.Session, building_data: dict, scenario_data: dict) -> dict:
    """Calculate building results for given building and scenario data."""
    data = {
        "newBuilding": building_data,
        "projectData": scenario_data["proj_json"],
    }
    response = session.post(f"{settings.NPRO_API}/calc_building", json=data)
    response.raise_for_status()
    result = response.json()
    if result["response"] != "success":
        raise RuntimeError("Could not load building data.")
    if settings.DEBUG:
        settings.save_debug_data(result["data"], "building")
    return result["data"]


def run_simulation(session: requests.Session, scenario_data: dict) -> None:
    """
    Run simulation with given scenario data.

    Must be called before calculating building results to update scenario data.
    """
    data = {
        "api_endpoint": "",
        "authenticated": True,
        "autoSaveProjects": 1,
        "calc_id": 53029542,
        "license": "academic",
        "BACKEND_VERSION": "4.0.0",
        "data": scenario_data["proj_json"],
    }
    response = session.post(f"{settings.NPRO_API}/calc_main", json=data)
    response.raise_for_status()
    run_data = response.json()
    if run_data["response"] != "success":
        raise RuntimeError("Could not run simulation.")
