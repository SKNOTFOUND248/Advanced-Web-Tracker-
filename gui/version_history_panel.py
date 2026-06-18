import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Callable
from models.version import WebsiteVersion

class VersionHistoryPanel(ttk.Frame):
    def __init__(self, parent, compare_callback: Callable[[int, int], None]):
        super().__init__(parent)
        self.compare_callback = compare_callback
        self.versions: List[WebsiteVersion] = []
        
        self._setup_ui()

    def _setup_ui(self):
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(header_frame, text="Version History", font=("TkDefaultFont", 10, "bold")).pack(side=tk.LEFT)
        
        self.btn_compare = ttk.Button(header_frame, text="Compare Selected", state=tk.DISABLED, command=self._on_compare)
        self.btn_compare.pack(side=tk.RIGHT)

        # Treeview
        columns = ("version", "date", "length", "resp_time", "hash")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="extended")
        
        self.tree.heading("version", text="Version")
        self.tree.heading("date", text="Date")
        self.tree.heading("length", text="Length")
        self.tree.heading("resp_time", text="Resp. Time")
        self.tree.heading("hash", text="Hash (short)")
        
        self.tree.column("version", width=60, anchor=tk.CENTER)
        self.tree.column("date", width=130)
        self.tree.column("length", width=80, anchor=tk.E)
        self.tree.column("resp_time", width=80, anchor=tk.E)
        self.tree.column("hash", width=100)
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.tree, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Events
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def update_versions(self, versions: List[WebsiteVersion]):
        self.versions = versions
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for v in self.versions:
            date_str = v.timestamp.strftime("%Y-%m-%d %H:%M:%S") if v.timestamp else "-"
            short_hash = v.content_hash[:8] if v.content_hash else "-"
            resp_str = f"{v.response_time:.2f}s" if v.response_time else "-"
            
            self.tree.insert("", tk.END, values=(v.version_number, date_str, v.content_length, resp_str, short_hash), tags=(str(v.id),))
            
        self._on_select(None) # Reset button state

    def _on_select(self, event):
        selected = self.tree.selection()
        if len(selected) == 2:
            self.btn_compare.config(state=tk.NORMAL)
        else:
            self.btn_compare.config(state=tk.DISABLED)

    def _on_compare(self):
        selected = self.tree.selection()
        if len(selected) != 2:
            messagebox.showinfo("Select Versions", "Please select exactly two versions to compare. (Use Ctrl+Click)")
            return
            
        id1 = int(self.tree.item(selected[0], "tags")[0])
        id2 = int(self.tree.item(selected[1], "tags")[0])
        
        # Pass the older one first usually, but lets just pass both and let the callback sort it out
        self.compare_callback(id1, id2)
