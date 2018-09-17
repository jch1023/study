from bs4 import BeautifulSoup as bs
import urllib.request as req
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')

url = "https://finance.naver.com/sise/"
res = req.urlopen(url).read()
soup = bs(res, 'html.parser')

top10 = soup.select('#siselist_tab_0 > tr')

i = 1
for e in top10: #enumerate 사용안함 왜냐면 None일 경우에도 카운트가 되서
    if e.find('a') is not None: #None이 아닐경우 출력
        print(i, e.select_one('.tltle').string)  #tltle "l" 영어 엘
        i += 1
