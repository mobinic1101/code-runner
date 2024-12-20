from pathlib import Path
from sys import path

# append the base project directory to python path
BASE_DIR = Path(__file__).resolve().parent.parent
path.append(str(BASE_DIR))
