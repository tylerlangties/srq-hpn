from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[4]
API_ROOT = Path(__file__).resolve().parents[2]

ROOT_ENV_LOCAL_PATH = PROJECT_ROOT / ".env.local"
API_ENV_PATH = API_ROOT / ".env"

load_dotenv(dotenv_path=ROOT_ENV_LOCAL_PATH, override=False)
load_dotenv(dotenv_path=API_ENV_PATH, override=False)
