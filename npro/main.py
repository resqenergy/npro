"""Main module to run simulations."""
from __future__ import annotations

import argparse
import pprint

from npro import api, scenario


def list_projects() -> None:
    """List all projects."""
    session = api.setup_session()
    api.login(session)
    for project in api.get_list_of_projects(session):
        pprint.pp(project, indent=2)


def list_buildings() -> None:
    """List all buildings of a project."""
    session = api.setup_session()
    api.login(session)
    project_data = api.load_project(session)
    for building in api.get_list_of_buildings(project_data):
        pprint.pp(building, indent=2)


def run_scenario(args: argparse.Namespace) -> None:
    """Run simulation with given scenario data."""
    if args.scenario == "all":
        scenario_names = list(scenario.get_list_of_scenarios())
    else:
        scenario_names = [args.scenario_name]
    if args.building == "existing":
        building = None
    else:
        building = scenario.load_building(args.building)
    for scenario_name in scenario_names:
        scenario.calculate_building_for_scenario(scenario_name, building, force_creation=args.force)


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        prog="npro",
        description="Commands for NPRO building simulation.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List projects
    projects_parser = subparsers.add_parser("projects")
    projects_parser.set_defaults(func=list_projects)

    # List buildings
    projects_parser = subparsers.add_parser("buildings")
    projects_parser.set_defaults(func=list_buildings)

    # Run scenarios
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("scenario", nargs="?", default="all")
    run_parser.add_argument("building", nargs="?", default="existing")
    run_parser.add_argument("-f", "--force", action="store_true")
    run_parser.set_defaults(func=run_scenario)
    run_parser.set_defaults(func=run_scenario)

    args = parser.parse_args()
    if args.command in ("projects", "buildings"):
        args.func()
    else:
        args.func(args)


if __name__ == "__main__":
    main()