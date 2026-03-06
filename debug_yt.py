
from youtube_transcript_api import YouTubeTranscriptApi
import sys

video_id = "5jNIobMPY7I"
print(f"Testing transcript for {video_id}")

try:
    print("Trying YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])...")
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
    print("Success!")
    print(transcript[:5])
except Exception as e:
    print(f"Failed: {e}")

try:
    print("\nTrying YouTubeTranscriptApi.list_transcripts(video_id)...")
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    print("Success!")
    for t in transcript_list:
        print(f"Available: {t.language} ({t.language_code})")
except Exception as e:
    print(f"Failed: {e}")
