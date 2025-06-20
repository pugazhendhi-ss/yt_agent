from langchain.tools import tool
from pydantic import BaseModel, Field
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from typing import Optional
import os
from app.models.tool_model import TranscriptErrorResponse, TranscriptSuccessResponse

# Get absolute path to the root directory and set path to transcripts inside app/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))           # /path/to/project_root/app
TRANSCRIPTS_DIR = os.path.join(BASE_DIR, "..", "transcripts")  # /path/to/project_root/app/transcripts



# Schema for LangChain tool
class YouTubeTranscriptArgs(BaseModel):
    youtube_url: str = Field(..., description="A YouTube video URL (e.g., https://youtu.be/xyz or https://youtube.com/watch?v=xyz)")


# Utility: Extract YouTube video ID
def extract_video_id(url: str) -> Optional[str]:
    if "youtu.be" in url:
        return url.split("/")[-1].split("?")[0]
    elif "youtube.com" in url:
        query = urlparse(url).query
        return parse_qs(query).get('v', [None])[0]
    return None


# Utility: Fetch transcript as plain text
def get_plain_transcript(video_id: str):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        print(transcript)
        return " ".join([entry['text'] for entry in transcript])
    except Exception as e:
        print(f"[Tool] Error fetching transcript for {video_id}]: {e}")
        return None


# Utility: Save transcript to transcripts/{video_id}.txt
def save_transcript_to_file(video_id: str, transcript_text: str, directory: str = TRANSCRIPTS_DIR):
    try:
        os.makedirs(directory, exist_ok=True)  # Create transcripts/ dir if not exists
        file_path = os.path.join(directory, f"{video_id}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(transcript_text)
            print(f"[Tool] Transcript created")
        return True
    except Exception as e:
        print(f"Error occurred while fetching transcripts from youtube: {e}")
        return False


# LangChain tool wrapper
@tool("youtube_transcript_saver",
      args_schema=YouTubeTranscriptArgs,
      description="Fetch and save transcript of a YouTube video into transcripts/{video_id}.txt if not already saved.")
def fetch_video_transcript(youtube_url: str):
    """
    Tool to fetch and save YouTube video transcript as a plain .txt file.

    Args:
        youtube_url (str): The full YouTube video URL (short or long form)

    Returns:
        str: Status message indicating whether it was saved, skipped, or error
    """
    video_id = extract_video_id(youtube_url)
    if not video_id:
        return TranscriptErrorResponse(reason="video id not present in the URL or invalid youtube video URL provided")

    save_path = os.path.join(TRANSCRIPTS_DIR, f"{video_id}.txt")
    transcript_created = False
    if os.path.exists(save_path):
        print()
        with open(save_path, "r", encoding="utf-8") as f:
            transcript_text = f.read()
            print(f"[Tool] Transcript already exists at {save_path}")
        transcript_created = True
    else:
        transcript_text = get_plain_transcript(video_id)
        if transcript_text:
            transcript_created = save_transcript_to_file(video_id, transcript_text)

    if not transcript_created:
        return TranscriptErrorResponse(reason="Some error occurred while fetching the transcript from youtube API.")
    return TranscriptSuccessResponse(transcript_text=transcript_text)




