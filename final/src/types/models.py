from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

class SlideType(Enum):
    TITLE = "title"
    CONTENT = "content"
    SECTION = "section"
    CONCLUSION = "conclusion"

@dataclass
class SlideContent:
    slide_number: int
    title: str
    text_content: str
    slide_type: SlideType
    images: List[str]
    notes: Optional[str] = None

@dataclass
class PresentationData:
    title: str
    slides: List[SlideContent]
    total_slides: int
    metadata: Dict[str, Any]

@dataclass
class SuggestionItem:
    type: str  # "question" or "supplement"
    content: str
    relevance_score: float
    slide_number: int
    reasoning: str

@dataclass
class AnalysisResult:
    presentation: PresentationData
    suggestions: List[SuggestionItem]
    citations: List[Dict[str, str]]
    summary: str