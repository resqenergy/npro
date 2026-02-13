
import api
import settings


def test_building_by_name() -> None:
    building_name = "Wohngebäude Mehrfamilienhäuser"
    session = api.setup_session()
    api.login(session)
    project_data = api.load_scenario(session, settings.NPRO_PROJECT)
    building_data = api.get_building_by_name(project_data, building_name)
    assert isinstance(building_data, dict)
    assert len(building_data) > 10