from flask import Flask, request, jsonify
import requests
import random

app = Flask(__name__)

# List of public Cobalt instances (Privacy-focused YouTube downloaders)
# We use multiple in case one is down or blocked.
COBALT_INSTANCES = [
    "https://api.cobalt.tools",           # Official (Best, but sometimes strict)
    "https://cobalt.gaia.domains",        # Community Instance
    "https://cobalt.moskas.cyou",         # Community Instance
    "https://cobalt.kwiatekmiki.pl",      # Community Instance
]

@app.route('/api/extract', methods=['GET'])
def extract_video():
    video_url = request.args.get('url')
    
    if not video_url:
        return jsonify({"error": "Missing URL parameter"}), 400

    # 1. Prepare the request payload for Cobalt
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    payload = {
        "url": video_url,
        "vCodec": "h264",  # Ensure compatibility
        "vQuality": "720", # Good balance for mobile
        "aFormat": "mp3",  # Best audio compatibility
        "isAudioOnly": False
    }

    # 2. Try each instance until one works
    last_error = ""
    for base_url in COBALT_INSTANCES:
        try:
            # Cobalt API endpoint is usually at /api/json or root depending on version
            # We try the standard v7+ endpoint
            api_url = f"{base_url}/api/json"
            
            response = requests.post(api_url, json=payload, headers=headers, timeout=8)
            data = response.json()

            # 3. Check for success
            if response.status_code == 200 and 'url' in data:
                return jsonify({
                    "title": "Video Found", 
                    "stream_url": data['url'],
                    "source": base_url # Debug info to see which server worked
                })
            
            # If successful but "status" is "stream" or "redirect"
            if data.get('status') in ['stream', 'redirect', 'tunnel']:
                return jsonify({
                    "title": "Video Found",
                    "stream_url": data.get('url'),
                    "source": base_url
                })

        except Exception as e:
            last_error = str(e)
            continue # Try the next server

    # 4. If all fail
    return jsonify({
        "error": "All servers failed. YouTube might be blocking heavily right now.",
        "details": last_error
    }), 500

if __name__ == '__main__':
    app.run()
