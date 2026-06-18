import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import csv
import json

from config import APP_NAME, APP_VERSION, THEME_DARK
from database.database_manager import DatabaseManager
from tracker.monitor import MonitorService
from models.website import Website

from gui.dialogs import AddWebsiteDialog, SettingsDialog
from gui.website_list_panel import WebsiteListPanel
from gui.details_panel import DetailsPanel
from gui.version_history_panel import VersionHistoryPanel
from gui.change_viewer import ChangeViewerDialog
from gui.keyword_panel import KeywordPanel
from gui.stats_dashboard import StatsDashboard

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1000x700")
        self.minsize(800, 600)
        
        self.db = DatabaseManager()
        self.monitor = MonitorService()
        
        self._setup_style()
        self._build_menu()
        self._build_ui()
        
        self.monitor.start()
        
        # Load data
        self._refresh_websites()
        
        # Start queue poller
        self.after(1000, self._poll_queue)
        
        # Handle close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_style(self):
        style = ttk.Style(self)
        if THEME_DARK:
            # Simple dark theme approach using tk_setPalette and ttk styles
            self.tk_setPalette(background='#2b2b2b', foreground='#a9b7c6', 
                               activeBackground='#3c3f41', activeForeground='#a9b7c6')
            style.theme_use('clam')
            style.configure('.', background='#2b2b2b', foreground='#a9b7c6', fieldbackground='#3c3f41')
            style.configure('Treeview', background='#3c3f41', fieldbackground='#3c3f41', foreground='#a9b7c6')
            style.configure('Treeview.Heading', background='#4e5254', foreground='#a9b7c6')
            style.map('Treeview', background=[('selected', '#2f65ca')])
            style.configure('TButton', background='#4e5254')
            style.map('TButton', background=[('active', '#5e6264')])
            style.configure('TEntry', fieldbackground='#3c3f41', foreground='#a9b7c6')
        else:
            style.theme_use('clam')

    def _build_menu(self):
        menubar = tk.Menu(self)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Add Website...", command=self._show_add_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Export Report...", command=self._export_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Settings...", command=self._show_settings)
        tools_menu.add_command(label="Backup Database...", command=self._backup_db)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        self.config(menu=menubar)

    def _build_ui(self):
        # Main PanedWindow (Left/Right)
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left Panel (Website List + Stats)
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        # Website List
        self.website_list = WebsiteListPanel(left_frame, self._on_website_selected)
        self.website_list.pack(fill=tk.BOTH, expand=True)
        
        # Stats Dashboard
        self.stats_panel = StatsDashboard(left_frame, self.db)
        self.stats_panel.pack(fill=tk.X, pady=(10, 0))
        
        # Right Panel (Details + Keywords + History)
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=3)
        
        # Top section of right frame (Details + Keywords)
        top_right = ttk.Frame(right_frame)
        top_right.pack(fill=tk.X, pady=5)
        
        self.details_panel = DetailsPanel(
            top_right, 
            check_now_callback=self._check_now,
            toggle_monitoring_callback=self._toggle_monitoring,
            delete_callback=self._delete_website
        )
        self.details_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.keyword_panel = KeywordPanel(top_right, self.db)
        self.keyword_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # Bottom section of right frame (History)
        self.history_panel = VersionHistoryPanel(right_frame, self._compare_versions)
        self.history_panel.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # --- Polling & Refreshing ---
    def _poll_queue(self):
        while not self.monitor.update_queue.empty():
            msg = self.monitor.update_queue.get()
            if msg["type"] == "website_checked":
                self.status_var.set(f"Completed check for website ID {msg['website_id']}")
                self._refresh_websites()
                if self.details_panel.current_website and self.details_panel.current_website.id == msg['website_id']:
                    # Refresh history if we are viewing this website
                    self._on_website_selected(self.details_panel.current_website)
            elif msg["type"] == "check_error":
                self.status_var.set(f"Error checking website ID {msg['website_id']}: {msg['error']}")
                self.stats_panel.refresh()
                
        self.after(1000, self._poll_queue)

    def _refresh_websites(self):
        websites = self.db.get_websites()
        self.website_list.update_list(websites)
        self.stats_panel.refresh()

    def _on_website_selected(self, website: Website):
        # Refresh website from DB to get latest state
        updated_websites = [w for w in self.db.get_websites() if w.id == website.id]
        if updated_websites:
            w = updated_websites[0]
            self.details_panel.update_details(w)
            self.keyword_panel.update_keywords(w)
            
            versions = self.db.get_versions(w.id)
            self.history_panel.update_versions(versions)
        else:
            self.details_panel.update_details(None)
            self.keyword_panel.update_keywords(None)
            self.history_panel.update_versions([])

    # --- Actions ---
    def _show_add_dialog(self):
        dlg = AddWebsiteDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            w = Website(
                name=dlg.result["name"],
                url=dlg.result["url"],
                check_interval=dlg.result["interval"],
                similarity_threshold=dlg.result["threshold"],
                keywords=dlg.result["keywords"]
            )
            wid = self.db.add_website(w)
            if wid:
                w.id = wid
                self.monitor.schedule_website(w)
                self._refresh_websites()
                self.status_var.set(f"Added website {w.name}")

    def _show_settings(self):
        SettingsDialog(self, self.db)

    def _check_now(self, website_id: int):
        self.status_var.set(f"Checking website ID {website_id}...")
        self.monitor.trigger_check_now(website_id)

    def _toggle_monitoring(self, website: Website):
        website.monitoring_enabled = not website.monitoring_enabled
        if self.db.update_website(website):
            if website.monitoring_enabled:
                self.monitor.schedule_website(website)
                self.status_var.set(f"Resumed monitoring {website.name}")
            else:
                self.monitor.unschedule_website(website.id)
                self.status_var.set(f"Paused monitoring {website.name}")
            self._refresh_websites()
            self._on_website_selected(website)

    def _delete_website(self, website_id: int):
        if self.db.delete_website(website_id):
            self.monitor.unschedule_website(website_id)
            self._refresh_websites()
            self.details_panel.update_details(None)
            self.keyword_panel.update_keywords(None)
            self.history_panel.update_versions([])
            self.status_var.set("Website deleted.")

    def _compare_versions(self, id1: int, id2: int):
        v1 = self.db.get_version_by_id(id1)
        v2 = self.db.get_version_by_id(id2)
        
        if not v1 or not v2:
            messagebox.showerror("Error", "Could not load version details from database.")
            return
            
        # Ensure v1 is the older version
        if v1.version_number > v2.version_number:
            v1, v2 = v2, v1
            
        ChangeViewerDialog(self, v1.content, v2.content, v1.version_number, v2.version_number)

    def _export_report(self):
        if not self.details_panel.current_website:
            messagebox.showinfo("Export", "Please select a website first.")
            return
            
        site = self.details_panel.current_website
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("JSON Files", "*.json"), ("Text Files", "*.txt")],
            title="Export Report"
        )
        
        if not file_path:
            return
            
        versions = self.db.get_versions(site.id)
        
        try:
            if file_path.endswith('.json'):
                data = {
                    "website": site.name,
                    "url": site.url,
                    "versions": [{"version": v.version_number, "date": str(v.timestamp), "hash": v.content_hash, "response_time": v.response_time} for v in versions]
                }
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                    
            elif file_path.endswith('.csv'):
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Version", "Date", "Content Length", "Response Time", "Hash"])
                    for v in versions:
                        writer.writerow([v.version_number, v.timestamp, v.content_length, v.response_time, v.content_hash])
                        
            else: # .txt
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Report for {site.name} ({site.url})\n")
                    f.write("="*40 + "\n")
                    for v in versions:
                        f.write(f"v{v.version_number} - {v.timestamp} | Length: {v.content_length} | Hash: {v.content_hash}\n")
                        
            messagebox.showinfo("Success", f"Report exported successfully to\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export report:\n{e}")

    def _backup_db(self):
        backup_dir = Path("data/backups")
        if self.db.backup_database(backup_dir):
            messagebox.showinfo("Backup", f"Database backed up successfully to {backup_dir.absolute()}")
        else:
            messagebox.showerror("Backup", "Database backup failed. Check logs.")

    def _on_close(self):
        self.monitor.stop()
        self.destroy()
