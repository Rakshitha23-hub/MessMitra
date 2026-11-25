
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE = os.path.join(
    BASE_DIR,
    "database",
    "messmitra.db"
)

SECRET_KEY = "messmitra-hackathon-secret-key"
