from flask import Flask, request, jsonify
import yt_dlp
import os
import tempfile
import base64
import random

app = Flask(__name__)

def get_cookies_path():
    cookies_content = os.environ.get('YOUTUBE_COOKIES')
    if not cookies_content:
        return None
    try:
        temp = tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.txt')
        decoded_content = base64.b64decode(cookies_content).decode('utf-8')
        temp.write(decoded_content)
        temp.close()
        return temp.name
    except Exception as e:
        return None

@app.route('/api/extract', methods=['GET'])
def extract_video():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "Missing URL parameter"}), 400

    cookie_file = get_cookies_path()
    
    # Get PO Token from Vercel Env Vars (Optional but Recommended)
    po_token = os.environ.get('YOUTUBE_PO_TOKEN')
    
    # 1. Setup Extractor Arguments to bypass bot checks
    # We tell YouTube we are an Android device or TV, which often bypasses the "Sign in" error.
    extractor_args = {
        'youtube': {
            'player_client': ['android', 'ios', 'web_embedded'],
            'player_skip': ['webpage', 'configs', 'js'], 
            'include_ssl_logs': [False] 
        }
    }
    
    # If you provide a PO Token, we inject it here
    if po_token:
        # Format: web+<your_token_here>
        extractor_args['youtube']['po_token'] = [f'web+{po_token}']

    try:
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'cookiefile': cookie_file,
            'extractor_args': extractor_args,
            # Use a generic mobile user agent
            'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'socket_timeout': 15,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            return jsonify({
                "title": info.get('title', 'Unknown'),
                "stream_url": info.get('url', None),
                "thumbnail": info.get('thumbnail', None),
                "duration": info.get('duration', None)
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cookie_file and os.path.exists(cookie_file):
            os.remove(cookie_file)

if __name__ == '__main__':
    app.run()
