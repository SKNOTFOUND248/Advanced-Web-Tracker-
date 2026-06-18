import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any

class AddWebsiteDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add Website")
        self.geometry("400x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.result: Optional[Dict[str, Any]] = None

        self._setup_ui()

    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Name
        ttk.Label(main_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, pady=5)

        # URL
        ttk.Label(main_frame, text="URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.url_var, width=40).grid(row=1, column=1, pady=5)

        # Interval
        ttk.Label(main_frame, text="Check Interval (mins):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.interval_var = tk.IntVar(value=10)
        ttk.Combobox(main_frame, textvariable=self.interval_var, values=[1, 5, 10, 30, 60], width=10, state="readonly").grid(row=2, column=1, sticky=tk.W, pady=5)

        # Threshold
        ttk.Label(main_frame, text="Similarity Threshold:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.threshold_var = tk.DoubleVar(value=0.95)
        ttk.Entry(main_frame, textvariable=self.threshold_var, width=10).grid(row=3, column=1, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text="(0.0 to 1.0, default 0.95)", font=("TkDefaultFont", 8)).grid(row=3, column=1, sticky=tk.E, pady=5)

        # Keywords
        ttk.Label(main_frame, text="Keywords (comma separated):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.keywords_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.keywords_var, width=40).grid(row=4, column=1, pady=5)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Add", command=self._on_add).pack(side=tk.LEFT, padx=5)

    def _on_add(self):
        name = self.name_var.get().strip()
        url = self.url_var.get().strip()
        
        if not name or not url:
            messagebox.showerror("Error", "Name and URL are required.", parent=self)
            return
            
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        try:
            interval = int(self.interval_var.get())
            threshold = float(self.threshold_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid interval or threshold.", parent=self)
            return

        kws = [k.strip() for k in self.keywords_var.get().split(",") if k.strip()]

        self.result = {
            "name": name,
            "url": url,
            "interval": interval,
            "threshold": threshold,
            "keywords": kws
        }
        self.destroy()

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Global Settings")
        self.geometry("300x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Placeholder for global settings if needed later
        ttk.Label(self, text="Global Settings (Coming Soon)", font=("TkDefaultFont", 12)).pack(pady=50)
        ttk.Button(self, text="Close", command=self.destroy).pack()
