import requests

def search_wikipedia(query):
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "opensearch",
        "search": query,
        "limit": 5,
        "namespace": 0,
        "format": "json"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()[1]  # list of titles

def get_summary(title):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return data.get("extract", "No summary found.")
