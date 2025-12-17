import requests
import uuid
import datetime
from bs4 import BeautifulSoup
# # url = 'https://jsonplaceholder.typicode.com/posts'
# url = 'https://example.com/'
# response = requests.get(url, timeout=10)
# print(f'HEADERS -> {response.headers}')
# print('\nJSON\n')
# # print(f'Data -> {response.json()}')
# print('\n')
# bond = response.raise_for_status()
# print(bond)

# print(f'STATUS CODE -> {response.status_code}')
# print(f'RESPONSE TEXT -> {response.text}')
# soup = BeautifulSoup(response.text, "html.parser")

# print(f'SOUP -> {soup}')
# title = soup.title.string if soup.title else None
# print(F'TITLE -> {title}')
# links_count = len(soup.find_all("a"))

# print(f'COUNT OF THE LINKS ->{links_count} ')


def scrape_url(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    link_counts = len(soup.find_all("a"))
    title = soup.title.string if soup.title else None
    get_id = uuid.uuid4()

    return {
        # 'id':str(get_id),
        # 'url':url,
        'status':response.status_code,
        'result': {
                   "title" : title,
                   "link_counts":link_counts
                  },
        # 'error_field': response.raise_for_status() if response.raise_for_status() else None,
        # 'date_created': datetime.datetime.now()
    }

'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField()
    status = models.CharField(max_length=25)
    result = models.JSONField(null=True, blank=True)
    error_field = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
'''