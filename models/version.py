from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class WebsiteVersion:
    website_id: int
    version_number: int
    content: str
    content_hash: str
    content_length: int
    response_time: float
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    previous_version_id: Optional[int] = None
    
    def compare_with_previous(self, previous_version: 'WebsiteVersion'):
        \"\"\"
        Compares this version with a previous version.
        Delegates to ChangeDetector in practice, but this is a stub for the model.
        \"\"\"
        pass
