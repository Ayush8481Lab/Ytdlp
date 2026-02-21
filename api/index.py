from http.server import BaseHTTPRequestHandler
import yt_dlp
import json
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the YouTube URL from the query string
        query = parse_qs(urlparse(self.path).query)
        video_url = query.get('url', [None])[0]

        if not video_url:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Please provide a YouTube ?url="}).encode('utf-8'))
            return

        # Configure yt-dlp to extract info without downloading
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                # Extract all formats (audio only, video only, combined)
                formats = []
                for f in info.get('formats', []):
                    formats.append({
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'), # mp4, webm, m4a
                        'resolution': f.get('resolution', 'audio only'),
                        'has_video': f.get('vcodec') != 'none',
                        'has_audio': f.get('acodec') != 'none',
                        'url': f.get('url') # The raw googlevideo direct link
                    })
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response_data = {
                    "title": info.get('title'),
                    "duration": info.get('duration'),
                    "formats": formats
                }
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
                
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
