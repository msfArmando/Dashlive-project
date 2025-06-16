from dotenv import load_dotenv
import os

load_dotenv()

class DbConnect:
    driver = os.getenv("DB_DRIVER")
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE")
    UID = os.getenv("DB_UID")
    PWD = os.getenv("DB_PWD")
