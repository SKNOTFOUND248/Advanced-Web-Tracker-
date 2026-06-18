import tkinter as tk
from tkinter import ttk
from database.database_manager import DatabaseManager

class StatsDashboard(ttk.Frame):
    def __init__(self, parent, db: DatabaseManager):
        super().__init__(parent)
        self.db = db
        self._setup_ui()

    def _setup_ui(self):
        ttk.Label(self, text="Global Overview", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, padx=5, pady=5)
        
        # Stats container
        stats_frame = ttk.Frame(self)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.lbl_total_sites = ttk.Label(stats_frame, text="Total Sites: -")
        self.lbl_total_sites.pack(anchor=tk.W)
        
        self.lbl_active_sites = ttk.Label(stats_frame, text="Active Monitoring: -")
        self.lbl_active_sites.pack(anchor=tk.W)
        
        # Recent Events List
        ttk.Label(self, text="Recent Events", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, padx=5, pady=(10, 5))
        
        self.tree = ttk.Treeview(self, columns=("time", "site", "event"), show="headings", height=5)
        self.tree.heading("time", text="Time")
        self.tree.heading("site", text="Website")
        self.tree.heading("event", text="Event")
        
        self.tree.column("time", width=120)
        self.tree.column("site", width=120)
        self.tree.column("event", width=150)
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.refresh()

    def refresh(self):
        # Update numbers
        websites = self.db.get_websites()
        self.lbl_total_sites.config(text=f"Total Sites: {len(websites)}")
        
        active = sum(1 for w in websites if w.monitoring_enabled)
        self.lbl_active_sites.config(text=f"Active Monitoring: {active}")
        
        # Update events
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        events = self.db.get_recent_events(limit=10)
        for e in events:
            # e is a dict from row factory
            time_str = e['timestamp']
            if not isinstance(time_str, str):
                time_str = time_str.strftime("%m-%d %H:%M:%S")
            else:
                time_str = time_str[5:16] # extract MM-DD HH:MM
                
            self.tree.insert("", tk.END, values=(time_str, e['website_name'], e['event_type']))
