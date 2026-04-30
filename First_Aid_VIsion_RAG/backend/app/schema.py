from pydantic import BaseModel, Field


class VisionAnalysis(BaseModel):
    summary: str = Field(..., description="Visible injury summary in Korean")
    injury_type: str = Field(..., description="Most likely first-aid category")
    urgency: str = Field(..., description="low, medium, or high")
    first_aid_focus: str = Field(..., description="Immediate first-aid focus in Korean")
    search_keywords: list[str] = Field(default_factory=list, description="RAG lookup keywords")
