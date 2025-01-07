import json
import os


SETTINGS_PATH = os.environ.get("LEETCODE_SETTINGS_PATH")


def get_settings(path):
    try:
        with open(path, "r") as file:
            return json.load(file)
    except Exception:
        return {}
    
settings_dict = get_settings(SETTINGS_PATH)

FASTAPI_HOST = settings_dict.get("fastapi_host", "localhost")
FASTAPI_PORT = int(settings_dict.get("fastapi_port", 5000))
REDIS_HOST = settings_dict.get("redis_host", "localhost")
REDIS_PORT = int(settings_dict.get("redis_port", 6379))
REDIS_EXPIRE_SEC = int(settings_dict.get("redis_expire_sec", 10))
RUN_TESTS_TIMEOUT = int(settings_dict.get("run_tests_timeout", 5))
# print("RUN_TESTS_TIMEOUT: ", RUN_TESTS_TIMEOUT)
