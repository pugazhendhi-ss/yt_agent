from pydantic import BaseModel, Field


class ArticleData(BaseModel):
    user_id: str = Field(..., description="unique id of that user")
    user: str = Field(..., description="article generated by the LLM")

class TranscriptSuccessResponse(BaseModel):
    status: str = "success"
    transcript_text: str
    next_action: str = "use this transcript to generate response as per the user's query"


class TranscriptErrorResponse(BaseModel):
    status: str = "error"
    reason: str
    transcript_text: str = "not generated, because of the error"
    next_action: str = "Tell the user that there is an error while fetching the data from youtube"


