
import requests
import settings


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


def load_scenario(session: requests.Session, project: str) -> dict:
    """Load scenario data for given project."""
    response = session.post(
        f"{settings.NPRO_API}/load_scenario", json={"projectStr": project}
    )
    response.raise_for_status()
    data = response.json()
    if data["server_msg"] != "scenarioLoaded":
        raise RuntimeError("Could not load scenario.")
    if settings.DEBUG:
        settings.save_debug_data(data["data"], "scenario")
    settings.logger.info(f"Successfully loaded scenario '{project}'.")
    return data["data"]


def calc_building(session: requests.Session, building_data: dict, scenario_data: dict) -> dict:
    """Calculate building results for given building and scenario data."""
    data = {
        "newBuilding": building_data,
        "projectData": scenario_data["proj_json"],
    }
    response = session.post(f"{settings.NPRO_API}/calc_building", json=data)
    response.raise_for_status()
    data = response.json()
    if data["response"] != "success":
        raise RuntimeError("Could not load building data.")
    if settings.DEBUG:
        settings.save_debug_data(data["data"], "building")
    return data["data"]


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


if __name__ == "__main__":
    _session = requests.Session()
    login(_session)
    _projects = get_list_of_projects(_session)
    _scenario_data = load_scenario(_session, "2591-0-0")

    building = _scenario_data["proj_json"]["buildingList"]["0"]
    # Original results
    results_orig = calc_building(_session, building, _scenario_data)

    # Change Temperature and rerun simulation
    _scenario_data["proj_json"]["airTemp"] = [2] * 8760
    run_simulation(_session, _scenario_data)

    results_changed = calc_building(_session, building, _scenario_data)

    diffs = {key: (value, results_changed[key]) for key, value in results_orig.items() if results_changed[key] != value}
    settings.save_debug_data(diffs, "diff")
