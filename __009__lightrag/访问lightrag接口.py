import requests
url = "http://localhost:9621/graph/label/list"
# data = {
#     "query": "阿胶鸡子黄汤包含什么药材",
#     "mode": "mix",
#     "stream": True,
#     "include_references": True
# }
result = requests.get(url=url)
print(result.json())
