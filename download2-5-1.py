from urllib.parse import urljoin

baseUrl = 'http://test.com/html/a.html'
print(">>", urljoin(baseUrl, "b.html"))
