import sys
import io
import urllib.request as dw

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')

imgUrl1 ="https://ssl.pstatic.net/tveta/libs/1202/1202505/e0322c01aa22392aa37b_20180914183550113.jpg"
imgUrl2 = "https://tvetamovie.pstatic.net/libs/1208/1208152/9b70d9abc02c160ecd0b_20180910100913892.mp4-pBASE-v0-f63863-20180910101712591.mp4"
#https://nv.veta.naver.com/fxshow?su=SU10078&nrefreshx=0

savePath1 ="c:/test1.jpg"
savePath2 ="c:/test2.mp4"


f = dw.urlopen(imgUrl1).read()
f2 = dw.urlopen(imgUrl2).read()


with open(savePath1,'wb') as saveFile1:
    saveFile1.write(f)

with open(savePath2,'wb') as saveFile2:
    saveFile2.write(f2)

#saveFile2 = open(savePath2, 'wb')
#saveFile2.write(f2)
#saveFile2.close


print("다운로드 완료!")
