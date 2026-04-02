"""Module to run requests against NPRO API."""

import requests

from npro import settings


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
        settings.save_debug_data(data["data"]["project_list"], "project_list")
    return data["data"]["project_list"]


def get_list_of_buildings(project_data: dict) -> list[dict]:
    """Return list of configured NPRO buildings."""
    return list(project_data["proj_json"]["buildingList"].values())


def get_default_building_data(building_type_data: dict) -> dict:
    """Return default building data."""
    response = requests.post(
        f"{settings.NPRO_API}/get_default_values",
        json=building_type_data,
    )
    response.raise_for_status()
    result = response.json()
    if result["response"] != "success":
        raise RuntimeError("Could not load building data.")
    return result["data"]

def load_project(session: requests.Session, project: str = settings.NPRO_PROJECT) -> dict:
    """Load scenario data for given project."""
    if project is None:
        raise KeyError("Project not found. You can set it using env var NPRO_PROJECT.")
    response = session.post(
        f"{settings.NPRO_API}/load_scenario", json={"projectStr": project}
    )
    response.raise_for_status()
    data = response.json()
    if data["server_msg"] != "scenarioLoaded":
        raise RuntimeError("Could not load project '{project}'.")
    if settings.DEBUG:
        settings.save_debug_data(data["data"], "project")
    settings.logger.info(f"Successfully loaded project '{settings.NPRO_PROJECT}'.")
    return data["data"]


def calc_building(session: requests.Session, building_data: dict, project_data: dict) -> dict:
    """Calculate building results for given building and scenario data."""
    data = {
        "newBuilding": building_data,
        "projectData": project_data["proj_json"],
    }
    response = session.post(f"{settings.NPRO_API}/calc_building", json=data)
    response.raise_for_status()
    result = response.json()
    if result["response"] != "success":
        raise RuntimeError("Could not load building data.")
    if settings.DEBUG:
        settings.save_debug_data(result["data"], "building_result")
    return result["data"]


def run_simulation(session: requests.Session, project_data: dict) -> None:
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
        "BACKEND_VERSION": "4.3.0",
        "data": project_data["proj_json"],
    }
    response = session.post(f"{settings.NPRO_API}/calc_main", json=data)
    response.raise_for_status()
    run_data = response.json()
    if run_data["response"] != "success":
        raise RuntimeError("Could not run simulation.")
