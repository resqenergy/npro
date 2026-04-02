
import api
import scenario


def test_building_by_name() -> None:
    building_name = "Wohngebäude Mehrfamilienhäuser"
    session = api.setup_session()
    api.login(session)
    project_data = api.load_project(session)
    building_list = list(project_data["proj_json"]["buildingList"].values())
    building_data = scenario.get_building_by_name(building_list, building_name)
    assert isinstance(building_data, dict)
    assert len(building_data) > 10