import sys
from youtube_transcript_api import YouTubeTranscriptApi

video_id = "OxnIz02VlH4"
print(f"Testing YouTubeTranscriptApi for video: {video_id}")

try:
    print(f"\nTrying with an instance: api = YouTubeTranscriptApi()...")
    api = YouTubeTranscriptApi()
    
    try:
        print(f"Trying api.list('{video_id}')...")
        transcripts = api.list(video_id)
        print("Success with api.list()!")
        
        try:
            print(f"Found transcript! fetching...")
            # Use 'ko' for this video specifically
            transcript = transcripts.find_generated_transcript(['ko'])
            data = transcript.fetch()
            print(f"Success! Fetched {len(data)} segments.")
            print(f"Data type: {type(data)}")
            
            if len(data) > 0:
                segment = data[0]
                print(f"First segment type: {type(segment)}")
                print(f"First segment attributes: {dir(segment)}")
                
                # Check for dictionary access vs attribute access
                try:
                    print(f"Trying segment['text']: {segment['text'][:50]}...")
                except Exception as e:
                    print(f"Error segment['text']: {e}")
                
                try:
                    print(f"Trying segment.text: {segment.text[:50]}...")
                except Exception as e:
                    print(f"Error segment.text: {e}")
                    
                # Bonus: check for other common keys
                keys = ['start', 'duration']
                for k in keys:
                    try:
                        print(f"segment['{k}']: {segment[k]}")
                    except:
                        pass
                    try:
                        print(f"segment.{k}: {getattr(segment, k)}")
                    except:
                        pass
        except Exception as e:
            print(f"Error within transcript processing: {e}")
            
    except Exception as e:
        print(f"Error api.list(): {e}")

except Exception as e:
    print(f"Error creating instance: {e}")
