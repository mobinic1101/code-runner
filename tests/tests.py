import requests


res = requests.get("http://localhost:5000/scheme")
print(res)


def test_run():
    requests.post("localhost:8000")