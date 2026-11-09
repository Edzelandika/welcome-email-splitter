"""Portable Windows interface for the shared Excel splitter."""
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from tkinterdnd2 import DND_FILES, COPY, REFUSE_DROP, TkinterDnD

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from split_emails import split


class App:
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.title("Welcome Email Splitter")
        self.root.geometry("660x440")
        self.root.minsize(600, 420)
        self.busy = False
        self.results = queue.Queue()
        frame = ttk.Frame(self.root, padding=28)
        frame.pack(fill="both", expand=True)
        heading = ttk.Label(frame, text="Drop your welcome email workbook here",
                            font=("Segoe UI", 17, "bold"), wraplength=590)
        heading.pack(anchor="w", pady=(0, 18))
        description = ttk.Label(frame, text="The original Excel workbook will be split into two workbooks: "
            "STUDENTS ONLY and NON-STUDENTS. The original is replaced; no backup is kept.\n\n"
            "Both keep only First Name, Last Name, and Email. Close the workbook in Excel first.",
            wraplength=590)
        description.pack(anchor="w", pady=(0, 18))
        self.button = ttk.Button(frame, text="Choose Excel File…", command=self.choose)
        self.button.pack(anchor="w", pady=(0, 18))
        self.status = tk.StringVar(value="Ready for one .xlsx file.")
        status = ttk.Label(frame, textvariable=self.status, wraplength=590)
        status.pack(anchor="w", fill="x")
        for widget in (self.root, frame, heading, description, status, self.button):
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self.drop)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(100, self.poll)

    def choose(self):
        path = filedialog.askopenfilename(parent=self.root, title="Choose original workbook",
                                         filetypes=[("Excel workbook", "*.xlsx")])
        if path:
            self.start(path)

    def drop(self, event):
        if self.busy:
            return REFUSE_DROP
        paths = self.root.tk.splitlist(event.data)
        if len(paths) != 1:
            self.status.set("Please drop one .xlsx file at a time.")
            return REFUSE_DROP
        self.start(paths[0])
        return COPY

    def start(self, path):
        if self.busy:
            return
        self.busy = True
        self.button.state(["disabled"])
        self.status.set("Splitting " + Path(path).name + "…")
        def work():
            try:
                message = split(path)
            except PermissionError:
                message = "Could not write the files. Close the workbook in Excel and check folder permissions, then try again."
            except Exception as error:
                message = "Could not split the workbook.\n\n" + str(error)
            self.results.put(message)
        threading.Thread(target=work, daemon=False).start()

    def poll(self):
        try:
            self.status.set(self.results.get_nowait())
            self.busy = False
            self.button.state(["!disabled"])
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def close(self):
        if self.busy:
            return
        self.root.destroy()


if __name__ == "__main__":
    app = App()
    if "--smoke-test" in sys.argv:
        app.root.update()
        app.root.destroy()
    else:
        app.root.mainloop()
