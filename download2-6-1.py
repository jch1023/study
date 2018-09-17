from bs4 import BeautifulSoup as bs
import sys
import io
import re #regex

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')

html = """
<html><body>
  <ul>
    <li><a id="naver" href="http://www.naver.com">naver</a></li>
    <li><a href="http://www.daum.net">daum</a></li>
    <li><a href="https://www.google.com">google</a></li>
    <li><a href="https://www.tistory.com">tistory</a></li>
  </ul>
</body></html>
"""

soup = bs(html, 'html.parser')
print(soup.find(id='naver').string)
li = soup.findAll(href=re.compile(r'^https://')) #정규표현식 ^ : ^뒤에 오는 걸로 시작 하는 문자

for e in li:
    print(e.attrs['href']) # 태그 제거
