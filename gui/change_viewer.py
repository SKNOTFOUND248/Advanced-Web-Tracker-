import tkinter as tk
from tkinter import ttk
from tracker.change_detector import ChangeDetector

class ChangeViewerDialog(tk.Toplevel):
    def __init__(self, parent, v1_content: str, v2_content: str, v1_num: int, v2_num: int):
        super().__init__(parent)
        self.title(f"Diff: Version {v1_num} vs Version {v2_num}")
        self.geometry("800x600")
        self.transient(parent)
        
        self.v1_content = v1_content
        self.v2_content = v2_content
        
        self._setup_ui()
        self._compute_and_display()

    def _setup_ui(self):
        # Header Info
        self.header_frame = ttk.Frame(self, padding="10")
        self.header_frame.pack(fill=tk.X)
        
        self.lbl_sim = ttk.Label(self.header_frame, text="Similarity: Calculating...", font=("TkDefaultFont", 10, "bold"))
        self.lbl_sim.pack(side=tk.LEFT)
        
        # Text Widget with scrollbar
        text_frame = ttk.Frame(self)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.text_widget = tk.Text(text_frame, wrap=tk.NONE, font=("Consolas", 10))
        
        vsb = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_widget.yview)
        hsb = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=self.text_widget.xview)
        
        self.text_widget.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure tags for diff coloring
        self.text_widget.tag_configure("added", background="#e6ffe6", foreground="#006600")
        self.text_widget.tag_configure("removed", background="#ffe6e6", foreground="#660000", overstrike=True)
        self.text_widget.tag_configure("header", background="#f0f0f0", foreground="#333333", font=("Consolas", 10, "italic"))

    def _compute_and_display(self):
        # We do this quickly in the main thread as it's just strings
        report = ChangeDetector.generate_detailed_diff(self.v1_content, self.v2_content)
        
        self.lbl_sim.config(text=f"Similarity: {report.similarity_score * 100:.1f}%")
        
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        
        # If identical
        if report.similarity_score == 1.0:
            self.text_widget.insert(tk.END, "Contents are identical.")
            self.text_widget.config(state=tk.DISABLED)
            return

        # Show word stats
        stats = f"Added words: {len(report.added_words)} | Removed words: {len(report.removed_words)}\n\n"
        self.text_widget.insert(tk.END, stats, "header")
        
        # Process diff lines
        for line in report.diff_lines:
            if line.startswith('+ '):
                self.text_widget.insert(tk.END, line + '\n', "added")
            elif line.startswith('- '):
                self.text_widget.insert(tk.END, line + '\n', "removed")
            elif line.startswith('? '):
                pass # skip difflib's hint lines for cleaner view
            else:
                self.text_widget.insert(tk.END, line + '\n')
                
        self.text_widget.config(state=tk.DISABLED)
