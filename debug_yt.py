from youtube_transcript_api import YouTubeTranscriptApi
print(f"Dir: {dir(YouTubeTranscriptApi)}")
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    # Try the most standard way first
    print("Testing YouTubeTranscriptApi.get_transcript...")
    # This will fail if not existing
    print(f"Has get_transcript: {hasattr(YouTubeTranscriptApi, 'get_transcript')}")
    print(f"Has list_transcripts: {hasattr(YouTubeTranscriptApi, 'list_transcripts')}")
except Exception as e:
    print(f"Error: {e}")
