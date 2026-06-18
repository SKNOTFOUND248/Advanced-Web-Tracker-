import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List
from database.database_manager import DatabaseManager
from models.website import Website

class KeywordPanel(ttk.Frame):
    def __init__(self, parent, db: DatabaseManager):
        super().__init__(parent)
        self.db = db
        self.current_website: Optional[Website] = None
        self._setup_ui()

    def _setup_ui(self):
        # Header
        ttk.Label(self, text="Keywords", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, padx=5, pady=5)
        
        # Add keyword frame
        add_frame = ttk.Frame(self)
        add_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.kw_var = tk.StringVar()
        self.entry_kw = ttk.Entry(add_frame, textvariable=self.kw_var)
        self.entry_kw.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry_kw.bind("<Return>", lambda e: self._on_add())
        
        self.btn_add = ttk.Button(add_frame, text="Add", command=self._on_add, state=tk.DISABLED)
        self.btn_add.pack(side=tk.RIGHT, padx=(5,0))

        # Listbox for keywords
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.listbox = tk.Listbox(list_frame, height=5)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Delete btn
        self.btn_del = ttk.Button(self, text="Remove Selected", command=self._on_remove, state=tk.DISABLED)
        self.btn_del.pack(pady=5)

    def update_keywords(self, website: Optional[Website]):
        self.current_website = website
        self.listbox.delete(0, tk.END)
        
        if not website:
            self.btn_add.config(state=tk.DISABLED)
            self.btn_del.config(state=tk.DISABLED)
            return
            
        self.btn_add.config(state=tk.NORMAL)
        self.btn_del.config(state=tk.NORMAL)
        
        kws = self.db.get_keywords(website.id)
        for kw in kws:
            self.listbox.insert(tk.END, kw)

    def _on_add(self):
        if not self.current_website:
            return
        kw = self.kw_var.get().strip()
        if not kw:
            return
            
        if self.db.add_keyword(self.current_website.id, kw):
            self.kw_var.set("")
            self.update_keywords(self.current_website)
            # Re-fetch the website to update its cached keywords so the monitor sees it
            self.current_website.keywords = self.db.get_keywords(self.current_website.id)
        else:
            messagebox.showerror("Error", "Failed to add keyword.")

    def _on_remove(self):
        if not self.current_website:
            return
        selection = self.listbox.curselection()
        if not selection:
            return
            
        kw = self.listbox.get(selection[0])
        if self.db.remove_keyword(self.current_website.id, kw):
            self.update_keywords(self.current_website)
            self.current_website.keywords = self.db.get_keywords(self.current_website.id)
