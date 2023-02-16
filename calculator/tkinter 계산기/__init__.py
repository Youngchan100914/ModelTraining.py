from tkinter import *


def enter(btn):
    if btn == 'C':
        ent.delete(0, END)
    elif btn == '=':
        ans = eval(ent.get())
        ent.delete(0, END)
        ent.insert(0, ans)
    else:
        ent.insert(END, btn)


def quit():
    root.destroy()
    root.quit()


root = Tk()
root.title('계산기')
ent = Entry(root)
ent.insert(0, ' ')
ent.pack(pady=5)
buttons = ['7410', '852=', '963+', 'C/*-']
for col in buttons:
    frm = Frame(root)
    frm.pack(side=LEFT)
    for row in col:
        btn = Button(frm, text=row, command=(lambda char=row: enter(char)))
        btn.pack(fill=X, padx=5, pady=5)

root.mainloop()
