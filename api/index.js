from flask import Flask, request, jsonify
import yt_dlp
import os
import tempfile
import base64

app = Flask(__name__)

def get_cookies_path():
    # 1. Check if the environment variable exists
    cookies_content = os.environ.get('YOUTUBE_COOKIES')
    
    if not cookies_content:
        return None

    # 2. Decode base64 cookies and write to a temp file
    try:
        # Create a temp file that persists only for this function run
        temp = tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.txt')
        # We expect the env var to be Base64 encoded to handle newlines correctly
        decoded_content = base64.b64decode(cookies_content).decode('utf-8')
        temp.write(decoded_content)
        temp.close()
        return temp.name
    except Exception as e:
        print(f"Error processing cookies: {e}")
        return None

@app.route('/api/extract', methods=['GET'])
def extract_video():
    video_url = request.args.get('url')
    
    if not video_url:
        return jsonify({"error": "Missing URL parameter"}), 400

    cookie_file = get_cookies_path()

    try:
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'socket_timeout': 10,
            # Spoof User Agent to look like a standard browser
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }

        # If we successfully created a cookie file, use it
        if cookie_file:
            ydl_opts['cookiefile'] = cookie_file

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            direct_url = info.get('url', None)
            title = info.get('title', 'Unknown')
            thumbnail = info.get('thumbnail', None)
            
            # Clean up temp file
            if cookie_file and os.path.exists(cookie_file):
                os.remove(cookie_file)

            return jsonify({
                "title": title,
                "stream_url": direct_url,
                "thumbnail": thumbnail
            })

    except Exception as e:
        # Clean up temp file in case of error
        if cookie_file and os.path.exists(cookie_file):
            os.remove(cookie_file)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run()
