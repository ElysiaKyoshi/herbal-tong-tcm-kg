import requests
from bs4 import BeautifulSoup
import urllib.parse


def baidu_search(query, num=10):
    # 百度搜索URL
    url = "https://www.baidu.com/s"
    params = {"wd": query, "rn": num}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0 Safari/537.36"
    }

    # 发送请求
    response = requests.get(url, params=params, headers=headers)
    response.encoding = "utf-8"  # 避免中文乱码

    # print("获取到的文本信息：", response.text)
    #
    # print("*" * 100)

    # 解析HTML
    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    for item in soup.select("h3 a"):  # 百度搜索结果的标题在 h3 > a
        title = item.get_text()
        link = item.get("href")  # 百度会用跳转链接，需要再解析
        results.append({"title": title, "link": link})

    return results


if __name__ == "__main__":
    keyword = "男士健身"
    search_results = baidu_search(keyword, num=10)

    for idx, result in enumerate(search_results, 1):
        print(f"{idx}. {result['title']}\n   {result['link']}\n")
