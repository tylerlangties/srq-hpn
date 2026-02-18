from pathlib import Path

from dotenv import load_dotenv

_here = Path(__file__).resolve()
API_ROOT = _here.parents[2]
PROJECT_ROOT = _here.parents[4] if len(_here.parents) > 4 else _here.parents[-1]

ROOT_ENV_LOCAL_PATH = PROJECT_ROOT / ".env.local"
API_ENV_PATH = API_ROOT / ".env"

load_dotenv(dotenv_path=ROOT_ENV_LOCAL_PATH, override=False)
load_dotenv(dotenv_path=API_ENV_PATH, override=False)
