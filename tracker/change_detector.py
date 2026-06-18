import difflib
import re
from typing import Tuple, List, Dict, Set
from utils.hashing import generate_hash

class ChangeReport:
    def __init__(self, old_content: str, new_content: str):
        self.old_content = old_content
        self.new_content = new_content
        self.is_changed = False
        self.similarity_score = 1.0
        
        self.added_words: Set[str] = set()
        self.removed_words: Set[str] = set()
        
        # Lists of HTML-formatted or raw strings for diff viewer
        self.diff_lines: List[str] = []

class ChangeDetector:
    
    @staticmethod
    def hash_comparison(old_content: str, new_content: str) -> bool:
        """Fastest check: Compare SHA256 hashes."""
        if old_content is None or new_content is None:
            return True # Consider None as different
        return generate_hash(old_content) != generate_hash(new_content)

    @staticmethod
    def calculate_similarity(old_content: str, new_content: str) -> float:
        """Calculate a similarity score between 0.0 and 1.0 using difflib."""
        if not old_content and not new_content:
            return 1.0
        if not old_content or not new_content:
            return 0.0
        
        # To make it faster for huge texts, we can compare words rather than characters
        # But difflib works reasonably fast for typical web page text content.
        matcher = difflib.SequenceMatcher(None, old_content, new_content)
        return matcher.quick_ratio()

    @staticmethod
    def word_diff(old_content: str, new_content: str) -> Tuple[Set[str], Set[str]]:
        """Extract words that were added and removed."""
        if not old_content: old_content = ""
        if not new_content: new_content = ""
        
        # Simple word extraction using regex
        old_words = set(re.findall(r'\\b\\w+\\b', old_content.lower()))
        new_words = set(re.findall(r'\\b\\w+\\b', new_content.lower()))
        
        added = new_words - old_words
        removed = old_words - new_words
        return added, removed

    @staticmethod
    def generate_detailed_diff(old_content: str, new_content: str) -> ChangeReport:
        """Generate a full ChangeReport with line-by-line differences."""
        report = ChangeReport(old_content or "", new_content or "")
        
        if not old_content and not new_content:
            return report

        report.is_changed = ChangeDetector.hash_comparison(old_content, new_content)
        if not report.is_changed:
            return report

        report.similarity_score = ChangeDetector.calculate_similarity(old_content, new_content)
        report.added_words, report.removed_words = ChangeDetector.word_diff(old_content, new_content)

        # Generate diff lines
        d = difflib.Differ()
        old_lines = (old_content or "").splitlines()
        new_lines = (new_content or "").splitlines()
        
        report.diff_lines = list(d.compare(old_lines, new_lines))
        return report

    @staticmethod
    def check_keywords(content: str, keywords: List[str]) -> List[str]:
        """Check if any of the monitored keywords appear in the content."""
        if not content or not keywords:
            return []
            
        found_keywords = []
        content_lower = content.lower()
        
        for kw in keywords:
            # Using regex to find whole words only, avoiding partial matches
            pattern = r'\\b' + re.escape(kw.lower()) + r'\\b'
            if re.search(pattern, content_lower):
                found_keywords.append(kw)
                
        return found_keywords
