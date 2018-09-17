from bs4 import BeautifulSoup as bs
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')

html = """
<html><body>
  <ul>
    <li><a href="http://www.naver.com">naver</a></li>
    <li><a href="http://www.daum.net">daum</a></li>
    <li><a href="https://www.google.com">google</a></li>
    <li><a href="https://www.tistory.com">tistory</a></li>
  </ul>
</body></html>
"""

soup = bs(html, 'html.parser')

links = soup.find_all('a')
#print('links', type(links))
a = soup.find_all('a',string='daum') #스트링이 daum 인것만 가져옴
#print('a',a)

b = soup.findAll('a', limit=[2])
#print(b)

c = soup.findAll(string=['naver', 'google']) #정규 표현식으로 나중에

for a in links:
    #print('a',type(a),a)
    href = a.attrs['href'] #키를 넣으면 벨류랑 같이 딕셔서리
    txt = a.string
    #print('txt >> ',txt,'href >>',href)
