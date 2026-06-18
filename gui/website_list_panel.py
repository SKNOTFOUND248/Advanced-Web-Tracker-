import tkinter as tk
from tkinter import ttk
from typing import Callable, List
from models.website import Website

class WebsiteListPanel(ttk.Frame):
    def __init__(self, parent, on_select_callback: Callable[[Website], None]):
        super().__init__(parent)
        self.on_select_callback = on_select_callback
        self.websites: List[Website] = []
        
        self._setup_ui()

    def _setup_ui(self):
        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(toolbar, text="Monitored Websites", font=("TkDefaultFont", 10, "bold")).pack(side=tk.LEFT)
        
        # Treeview
        columns = ("name", "status", "interval")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("name", text="Name")
        self.tree.heading("status", text="Status")
        self.tree.heading("interval", text="Interval")
        
        self.tree.column("name", width=150)
        self.tree.column("status", width=80, anchor=tk.CENTER)
        self.tree.column("interval", width=80, anchor=tk.CENTER)
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.tree, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Events
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def update_list(self, websites: List[Website]):
        self.websites = websites
        
        # Remember selection
        selected_item = self.tree.selection()
        selected_id = None
        if selected_item:
            selected_id = self.tree.item(selected_item[0], "tags")[0]

        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Repopulate
        for w in self.websites:
            status = "Active" if w.monitoring_enabled else "Paused"
            item_id = self.tree.insert("", tk.END, values=(w.name, status, f"{w.check_interval}m"), tags=(str(w.id),))
            
            # Restore selection
            if selected_id == str(w.id):
                self.tree.selection_set(item_id)

    def _on_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
            
        item_id = selected_items[0]
        website_id_str = self.tree.item(item_id, "tags")[0]
        
        for w in self.websites:
            if str(w.id) == website_id_str:
                self.on_select_callback(w)
                break
