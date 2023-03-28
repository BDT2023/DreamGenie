from tkinter import *

class CustomWindow:
    def __init__(self, master):
        self.master = master
        master.title("Custom Window")

        # Create a text box
        self.textbox = Entry(master, width=50)
        self.textbox.pack(padx=10, pady=10)

        # Create a Cancel button
        self.cancel_button = Button(master, text="Cancel", command=self.cancel)
        self.cancel_button.pack(side=LEFT, padx=10, pady=10)

        # Create a Next button
        self.next_button = Button(master, text="Next", command=self.next, state=DISABLED)
        self.next_button.pack(side=RIGHT, padx=10, pady=10)

        # Set up an event listener to check for changes in the text box
        self.textbox.bind("<KeyRelease>", self.check_text)

    def check_text(self, event):
        # Enable the Next button if the text box contains some text
        if len(self.textbox.get()) > 0:
            self.next_button.config(state=NORMAL)
        else:
            self.next_button.config(state=DISABLED)

    def cancel(self):
        # Close the window when Cancel is clicked
        self.master.destroy()

    def next(self):
        # Do something when Next is clicked
        print(self.textbox.get())
        

root = Tk()
custom_window = CustomWindow(root)
root.mainloop()