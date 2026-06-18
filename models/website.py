from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class Website:
    url: str
    name: str
    id: Optional[int] = None
    monitoring_enabled: bool = True
    check_interval: int = 10  # minutes
    similarity_threshold: float = 0.95
    created_at: Optional[datetime] = None
    
    # State fields (not always persisted in the main website row, but useful for UI)
    keywords: List[str] = field(default_factory=list)
    last_checked: Optional[datetime] = None
    current_hash: Optional[str] = None
    response_time: Optional[float] = None
    
    def enable(self):
        self.monitoring_enabled = True
        
    def disable(self):
        self.monitoring_enabled = False
