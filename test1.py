from tkinter import *

def printHello():
    print('fucker')

root = Tk()

w = Label(root, text="pytion Test")
b = Button(root, text="눌러봐", command=printHello)
c = Button(root, text="꺼져", command=root.quit)

w.pack()
b.pack()
c.pack()

root.mainloop()
