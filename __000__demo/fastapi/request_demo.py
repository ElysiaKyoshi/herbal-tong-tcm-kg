import requests

url = "http://127.0.0.1:8000/process"
payload = {"name": "Alice", "age": 25}

res = requests.post(url, json=payload)
print(res.json())
