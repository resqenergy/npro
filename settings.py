"""Module to configure project via env variables."""

import os
import json
import pathlib
from dotenv import load_dotenv
from loguru import logger
import uuid

load_dotenv()

ROOT_DIR = pathlib.Path(__file__).parent
SCENARIOS_DIR = ROOT_DIR / "scenarios"
RESULTS_DIR = ROOT_DIR / "results"

DEBUG = os.getenv("DEBUG", "False") == "True"
DEBUG_DIR = ROOT_DIR / "debug"
if DEBUG:
    logger.info("DEBUG MODE ENABLED")
    DEBUG_DIR.mkdir(exist_ok=True)

NPRO_API = "https://acad.npro.energy/api"
NPRO_EMAIL = os.getenv("NPRO_EMAIL")
NPRO_PASSWORD = os.getenv("NPRO_PASSWORD")
NPRO_PROJECT = os.getenv("NPRO_PROJECT")

if not (NPRO_EMAIL and NPRO_PASSWORD):
    raise ValueError("NPRO_EMAIL and NPRO_PASSWORD must be set")

if not NPRO_PROJECT:
    logger.info(f"NPRO Project not set (NPRO_PROJECT). You can use `uv run main.py list` to see available projects. ")

def save_debug_data(data: dict, name: str) -> None:
    save_name = f"{name}_{uuid.uuid4()}.json"
    with (DEBUG_DIR / save_name).open("w") as f:
        json.dump(data, f, indent=2)
    logger.debug(f"Saved {name} data as {DEBUG_DIR / save_name}.")
