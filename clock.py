import tkinter as tk
import time

def update_time():
    current_time = time.strftime('%H:%M:%S')
    clock_label.config(text=current_time)
    root.after(1000, update_time)  # Update every 1000 milliseconds (1 second)

root = tk.Tk()
root.title("Digital Clock")

# Set the window always on top
root.attributes("-topmost", True)

clock_label = tk.Label(root, text="", font=("Helvetica", 40))
clock_label.pack(padx=5, pady=5)

update_time()
root.mainloop()
