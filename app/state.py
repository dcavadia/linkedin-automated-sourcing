from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

class Candidate(BaseModel):
    linkedin_id: str = Field(..., description="Unique LinkedIn profile ID (hashed for privacy)")
    name: Optional[str] = Field(None, description="Candidate name (anonymized if needed)")
    profile_data: Dict[str, Any] = Field(default_factory=dict, description="Raw profile info: skills, experience, etc.")
    relevance_score: Optional[float] = Field(None, description="Relevance score (0-1)")
    message: Optional[str] = Field(None, description="Personalized outreach message")
    sent_at: Optional[datetime] = Field(None, description="Timestamp when message was sent")
    responses: List[str] = Field(default_factory=list, description="List of interaction responses")
    status: str = Field(default="pending", description="Status: 'pending', 'scored', 'ready_to_send', 'contacted', 'responded', 'rejected'")

class AppState(BaseModel):
    config: Dict[str, Any] = Field(default_factory=dict, description="Search filters: {'keywords': ['AI', 'ML'], 'min_exp': 3, 'location': 'Remote'}")
    candidates: List[Candidate] = Field(default_factory=list, description="List of discovered/filtered candidates")
    metrics: Dict[str, float] = Field(
        default_factory=lambda: {"response_rate": 0.0, "avg_score": 0.0, "total_processed": 0},
        description="Runtime metrics"
    )
    run_id: str = Field(default_factory=lambda: f"run_{datetime.now().isoformat()}", description="Unique run identifier for checkpointing")
