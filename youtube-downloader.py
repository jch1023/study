import pytube
import os
import subprocess

yturl = input('유투브주소를 입력하세요')

yt = pytube.YouTube(yturl) #다운 받은 동영상 다운
videos = yt.streams.all()

#print('videos',videos)

for i in range(len(videos)): #range(1,6) 1,2,3,4,5
    print(i, ',', videos[i])

cNum = int(input('다운 받을 화질은?(0~21 ENTER)'))

down_dir = 'c:/youtube'

videos[cNum].download(down_dir)

newFileName = input('변환 할 mp3 파일명은?')
oriFileName = videos[cNum].default_filename

subprocess.call(['ffmpeg', '-i',
    os.path.join(down_dir,oriFileName),
    os.path.join(down_dir,newFileName)
])

print('동영상 다운로드 및 mp3 변환 완료!')
