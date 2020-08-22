# -*- coding: utf-8 -*-
"""
Created on Mon Aug  3 20:57:43 2020

@author: DELL
"""

from tkinter import *

def makeform(root, fields):
   entries = {}
   #root.title("Network Optimiser")
   for field in fields:
      row = Frame(root)
      lab = Label(row, width=25, text=field+": ", anchor='w')
      ent = Entry(row)
      ent.insert(0,"")
      row.pack(side = TOP, fill = X, padx = 25 , pady = 15)
      lab.pack(side = LEFT)
      ent.pack(side = RIGHT, expand = YES, fill = X)
      entries[field] = ent
   return entries

if __name__ == '__main__':
    fields = ('Host', 'User', 'Password','DB') 
    root = Tk()
    label= Label(root)
    var = IntVar()
    ents = makeform(root, fields)
    root.bind('<Return>', (lambda event, e = ents: fetch(e)))
    b1 = Button(root, text = 'Connect & save',command=(lambda e = ents, d = nodb: GetValues(e,d)))
    b1.pack(side = LEFT, padx = 5, pady = 25)
    frame2 = Frame(root)
    frame2.pack(anchor=SE)
    rb1 = Radiobutton(frame2, text='Minimize Costs',variable = var,value=1, command = label.config(text = ''))
    rb1.pack(anchor=NE)
    rb2 = Radiobutton(frame2, text='Maximize Profits',variable = var,value=2, command = label.config(text = ''))
    rb2.pack(anchor=NE)
    b3 = Button(frame2, text = 'Run Model', command=(lambda e = ents, d = nodb: RunpyomoModel(e,d)))
    b3.pack(anchor=S)
    label.pack()
    bottomframe = Frame(root)
    bottomframe.pack(side = BOTTOM )
    ents1 = makeform(bottomframe,fields)
    root.mainloop()