from bs4 import BeautifulSoup as bs
import urllib.request as req
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')

url = "http://finance.daum.net/"
res = req.urlopen(url).read()
soup = bs(res, 'html.parser')

#print(soup.prettify())

top = soup.select('ul#topMyListNo1 > li')

#print(top) 확인 작업

for i,e in enumerate(top,1): #인덱스로 저장 top,1 1번부터 시작
#    print(type(e)) <class 'bs4.element.Tag'> 아직 끝나지 않은 상태 text 나 string 안됨
    print(i, ",", e.find('a').string)
