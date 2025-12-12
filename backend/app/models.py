from pydantic import BaseModel, EmailStr, HttpUrl, Field
from typing import Optional, Any, Dict, List, Union

class QuizRequest(BaseModel):
    email: EmailStr
    secret: str
    url: HttpUrl

class QuizResponse(BaseModel):
    status: str
    message: str

class QuizSubmission(BaseModel):
    email: EmailStr
    secret: str
    url: str # Using str because HttpUrl can be tricky with partials or if logic changes
    answer: Union[str, int, float, bool, Dict[str, Any]]

class LLMAction(BaseModel):
    action: str = Field(..., description="Action to take: 'code', 'download', 'submit', 'wait'")
    code: Optional[str] = None
    url: Optional[str] = None
    answer: Optional[Union[str, int, float, bool, Dict]] = None
    submit_url: Optional[str] = None
    reason: Optional[str] = None
