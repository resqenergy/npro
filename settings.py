import os
import json
import pathlib
from dotenv import load_dotenv
from loguru import logger
import uuid

load_dotenv()

ROOT_DIR = pathlib.Path(__file__).parent
SCENARIOS_DIR = ROOT_DIR / "scenarios"

DEBUG = os.getenv("DEBUG", "False") == "True"
DEBUG_DIR = ROOT_DIR / "debug"
if DEBUG:
    logger.info("DEBUG MODE ENABLED")
    DEBUG_DIR.mkdir(exist_ok=True)

NPRO_API = "https://acad.npro.energy/api"
NPRO_EMAIL = os.getenv("NPRO_EMAIL")
NPRO_PASSWORD = os.getenv("NPRO_PASSWORD")

if not (NPRO_EMAIL and NPRO_PASSWORD):
    raise ValueError("NPRO_EMAIL and NPRO_PASSWORD must be set")


def save_debug_data(data: dict, name: str) -> None:
    save_name = f"{name}_{uuid.uuid4()}.json"
    with (DEBUG_DIR / save_name).open("w") as f:
        json.dump(data, f, indent=2)
    logger.debug(f"Saved {name} data as {DEBUG_DIR / save_name}.")
