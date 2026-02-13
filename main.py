"""Main module to run simulations."""
from __future__ import annotations

import pprint

import api
import argparse

import scenario

NO_ARGS_FCT = ("list",)


def list_projects() -> None:
    """List all projects."""
    session = api.setup_session()
    api.login(session)
    for project in api.get_list_of_projects(session):
        pprint.pp(project, indent=2)


def run_scenario(args: argparse.Namespace) -> None:
    """Run simulation with given scenario data."""
    if args.scenario_name == "all":
        scenario_names = list(scenario.get_list_of_scenarios())
    else:
        scenario_names = [args.scenario_name]
    for scenario_name in scenario_names:
        scenario.calculate_building_for_scenario(scenario_name)


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        prog="npro",
        description="Commands for NPRO building simulation.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List projects
    projects_parser = subparsers.add_parser("list")
    projects_parser.set_defaults(func=list_projects)

    # Run scenarios
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("scenario_name", nargs="?", default="all")
    run_parser.set_defaults(func=run_scenario)

    args = parser.parse_args()
    if args.command in NO_ARGS_FCT:
        args.func()
    else:
        args.func(args)


if __name__ == "__main__":
    main()