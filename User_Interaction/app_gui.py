import tkinter as tk
from tkinter import messagebox

class HelloWorldWindow:
    def __init__(self, master):
        self.master = master
        

        # Create and place "Hello World" label at top middle
        hello_label = tk.Label(self.master, text="Hello World")
        hello_label.pack(side=tk.TOP)

        # Create and place "Cancel" button at bottom left
        cancel_button = tk.Button(self.master, text="Cancel", command=self.on_cancel)
        cancel_button.pack(side=tk.BOTTOM, padx=10, pady=10, anchor=tk.SW)

        # Create and place "Start Journey" button at bottom right
        start_button = tk.Button(self.master, text="Start Journey", command=self.on_start)
        start_button.pack(side=tk.BOTTOM, padx=10, pady=10, anchor=tk.SE)

    def on_cancel(self):
        # Display a messagebox asking if the user wants to cancel
        result = messagebox.askquestion("Cancel", "Are you sure you want to cancel?")
        if result == "yes":
            self.master.quit() # Exit the program
        else:
            pass # Do nothing and return to the window
        
    def clear_window(self):
        # Destroy all widgets in the window
        for widget in self.master.winfo_children():
            widget.destroy()

    def on_start(self):
        # Create and show the second window
        self.clear_window()
        self.second_window = FunWindow(self.master)

class FunWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Fun!!!")

        # Create and place "Fun!!!" label at top middle
        fun_label = tk.Label(self.master, text="Fun!!!")
        fun_label.pack(side=tk.TOP)

        # Create a text box
        self.text_box = tk.Text(self.master, height=5, width=50)
        self.text_box.pack(side=tk.TOP, pady=10)

        # Create and place "Submit" button
        submit_button = tk.Button(self.master, text="Submit", command=self.on_submit)
        submit_button.pack(side=tk.TOP)

    def on_submit(self):
        # Get the text from the text box and print it to the console
        text = self.text_box.get("1.0", "end-1c")
        print(text)

if __name__ == "__main__":
    root = tk.Tk()
    # size of the window
    root.geometry("400x300")
    app = HelloWorldWindow(root)
    root.mainloop()
