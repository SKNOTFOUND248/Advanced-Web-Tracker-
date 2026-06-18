import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from models.website import Website

class DetailsPanel(ttk.Frame):
    def __init__(self, parent, check_now_callback: Callable[[int], None], toggle_monitoring_callback: Callable[[Website], None], delete_callback: Callable[[int], None]):
        super().__init__(parent)
        self.check_now_callback = check_now_callback
        self.toggle_monitoring_callback = toggle_monitoring_callback
        self.delete_callback = delete_callback
        
        self.current_website: Optional[Website] = None
        self._setup_ui()

    def _setup_ui(self):
        # Header
        self.title_label = ttk.Label(self, text="Select a website to view details", font=("TkDefaultFont", 12, "bold"))
        self.title_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # Details Grid
        ttk.Label(self, text="URL:").grid(row=1, column=0, sticky=tk.E, pady=2, padx=5)
        self.url_label = ttk.Label(self, text="-", foreground="blue", cursor="hand2")
        self.url_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(self, text="Status:").grid(row=2, column=0, sticky=tk.E, pady=2, padx=5)
        self.status_label = ttk.Label(self, text="-")
        self.status_label.grid(row=2, column=1, sticky=tk.W, pady=2)

        ttk.Label(self, text="Last Checked:").grid(row=3, column=0, sticky=tk.E, pady=2, padx=5)
        self.last_checked_label = ttk.Label(self, text="-")
        self.last_checked_label.grid(row=3, column=1, sticky=tk.W, pady=2)

        ttk.Label(self, text="Response Time:").grid(row=4, column=0, sticky=tk.E, pady=2, padx=5)
        self.response_time_label = ttk.Label(self, text="-")
        self.response_time_label.grid(row=4, column=1, sticky=tk.W, pady=2)

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=15, sticky=tk.W)

        self.btn_check_now = ttk.Button(btn_frame, text="Check Now", state=tk.DISABLED, command=self._on_check_now)
        self.btn_check_now.pack(side=tk.LEFT, padx=2)

        self.btn_toggle = ttk.Button(btn_frame, text="Toggle Monitoring", state=tk.DISABLED, command=self._on_toggle)
        self.btn_toggle.pack(side=tk.LEFT, padx=2)
        
        self.btn_delete = ttk.Button(btn_frame, text="Delete", state=tk.DISABLED, command=self._on_delete)
        self.btn_delete.pack(side=tk.LEFT, padx=2)

    def update_details(self, website: Optional[Website]):
        self.current_website = website
        if not website:
            self.title_label.config(text="Select a website to view details")
            self.url_label.config(text="-")
            self.status_label.config(text="-")
            self.last_checked_label.config(text="-")
            self.response_time_label.config(text="-")
            self.btn_check_now.config(state=tk.DISABLED)
            self.btn_toggle.config(state=tk.DISABLED)
            self.btn_delete.config(state=tk.DISABLED)
            return

        self.title_label.config(text=website.name)
        self.url_label.config(text=website.url)
        self.status_label.config(text="Active" if website.monitoring_enabled else "Paused")
        
        if website.last_checked:
            self.last_checked_label.config(text=website.last_checked.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            self.last_checked_label.config(text="Never")
            
        if website.response_time:
            self.response_time_label.config(text=f"{website.response_time:.2f}s")
        else:
            self.response_time_label.config(text="-")

        self.btn_check_now.config(state=tk.NORMAL)
        self.btn_toggle.config(state=tk.NORMAL, text="Pause" if website.monitoring_enabled else "Resume")
        self.btn_delete.config(state=tk.NORMAL)

    def _on_check_now(self):
        if self.current_website:
            self.check_now_callback(self.current_website.id)

    def _on_toggle(self):
        if self.current_website:
            self.toggle_monitoring_callback(self.current_website)

    def _on_delete(self):
        if self.current_website:
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{self.current_website.name}' and all its history?"):
                self.delete_callback(self.current_website.id)
