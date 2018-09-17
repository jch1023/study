from bs4 import BeautifulSoup as bs
import urllib.request as req
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')

url = "https://www.daum.net"
res = req.urlopen(url).read()
soup = bs(res, 'html.parser')

rank = soup.select('div.rank_cont > span.txt_issue > a[tabindex="-1"]')
#print(rank)
for e in rank:
    print(e.string)
    print(e['href'])  #이미 e안에 a태그정보가 담겨 있으므로, a 태그의 href 속성 값을 가져옴
