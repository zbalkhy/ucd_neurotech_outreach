import tkinter as tk
import queue
import threading
import numpy as np

# example of multithreading in a tkinter app
# we will need this eventually

def runloop(thread_queue=None):
    result = 0
    for i in range(10000):
        thread_queue.put(i)
        #A = np.random.randn(100,100)
        #B = np.random.randn(100,100)
        #C = A*B
        #result += np.sum(C)
    result = result + 1
    thread_queue.put(result)

class MainApp():
    def __init__(self, root):
            super(MainApp,self).__init__()
            self.root = root
            self.frame = tk.Frame(self.root)
            self.frame.grid(row=0, column=0, sticky='nswe')
            self.mylabel = tk.Label(self.frame) # Element to be updated
            self.mylabel.config(text='No message')
            self.mylabel.grid(row=0, column=0)
            self.mybutton = tk.Button(
                                self.frame,
                                text='Change message111',
                                command=self.update_text)
            
            self.mybutton.grid(row=1, column=0)
            self.res = 0

    def update_text(self):
            self.mylabel.config(text='Running loop')
            self.thread_queue = queue.Queue()
            self.new_thread = threading.Thread(
                                target=runloop,
                                kwargs={'thread_queue':self.thread_queue})
            self.new_thread.start()
            self.root.after(100, self.listen_for_result)
    
    def listen_for_result(self):
            try:
                self.res += self.thread_queue.get()
                self.mylabel.config(text='Loop terminated' + str(self.res))
                self.root.after(1, self.listen_for_result)
            except queue.Empty:
                self.root.after(100, self.listen_for_result)

if __name__ == "__main__":
    root = tk.Tk()
    main_app = MainApp(root)
    root.mainloop()