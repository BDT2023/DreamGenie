import tkinter as tk

def get_user_input():
    root = tk.Tk()
    root.geometry("200x100")
    root.title("Yes or No")

    user_input = None

    def on_yes():
        nonlocal user_input
        user_input = "Yes"
        root.destroy()

    def on_no():
        nonlocal user_input
        user_input = "No"
        root.destroy()

    yes_button = tk.Button(root, text="Yes", command=on_yes)
    yes_button.pack(side=tk.LEFT, padx=20)

    no_button = tk.Button(root, text="No", command=on_no)
    no_button.pack(side=tk.RIGHT, padx=20)

    root.mainloop()

    return user_input
