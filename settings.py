import json

settings_path = "/etc/leetcode_backend.json"
with open(settings_path, "r") as file:
    settings_dict = json.load(file)

FASTAPI_HOST = settings_dict.get("fastapi_host", "localhost")
FASTAPI_PORT = int(settings_dict.get("fastapi_port", 5000))
REDIS_HOST = settings_dict.get("redis_host", "localhost")
REDIS_PORT = int(settings_dict.get("redis_port", 6379))
REDIS_EXPIRE_SEC = int(settings_dict.get("redis_expire_sec", 10))
RUN_TESTS_TIMEOUT = int(settings_dict.get("run_tests_timeout", 5))
print("RUN_TESTS_TIMEOUT: ", RUN_TESTS_TIMEOUT)
