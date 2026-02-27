from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import tempfile
import json
import subprocess

app = Flask(__name__)
# CORS allows your frontend to talk to this backend
CORS(app)

@app.route('/api/render', methods=['POST'])
def render_video():
    # 1. Check if video is in the request
    if 'video' not in request.files:
        return jsonify({"error": "No video provided"}), 400

    video_file = request.files['video']
    settings = json.loads(request.form.get('settings', '{}'))

    # 2. Create temporary files to hold the data
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as input_temp, \
         tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as output_temp:
        
        input_path = input_temp.name
        output_path = output_temp.name
        video_file.save(input_path)

    try:
        # 3. Extract the video settings mapped from the frontend
        v_settings = settings.get('video', {})
        
        # Build the video filter string
        video_filters = []
        if v_settings.get('flip'):
            video_filters.append('hflip')
            
        # Frontend brightness is 0-200, FFmpeg is -1.0 to 1.0
        brightness = (v_settings.get('brightness', 100) - 100) / 100.0
        video_filters.append(f'eq=brightness={brightness}')
        
        if v_settings.get('grayscale') == 100:
            video_filters.append('hue=s=0')
            
        v_filter_str = ','.join(video_filters) if video_filters else 'null'

        # 4. Build the FFmpeg Command
        # This creates a waveform visualizer and overlays it on the filtered video
        # Note: Replicating a complex HTML canvas perfectly requires tweaking this filtergraph
        command = [
            'ffmpeg', '-y', '-i', input_path,
            '-filter_complex', 
            f"[0:v]{v_filter_str}[vid];"                 # Apply video filters
            f"[0:a]showwaves=s=1280x200:mode=cline:colors=white[vis];" # Create visualizer
            f"[vid][vis]overlay=0:H-h[out]",             # Overlay visualizer at the bottom
            '-map', '[out]', '-map', '0:a',              # Map the final video and original audio
            '-c:v', 'libx264', '-preset', 'fast',        # Compress video
            '-c:a', 'aac',                               # Compress audio
            output_path
        ]

        # Run FFmpeg
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 5. Send the finished file directly to the user for download
        return send_file(
            output_path,
            as_attachment=True,
            download_name="ne_visualizer.mp4",
            mimetype="video/mp4"
        )

    except subprocess.CalledProcessError as e:
        print(f"FFmpeg Error: {e.stderr.decode()}")
        return jsonify({"error": "Failed to process video"}), 500
    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        # 6. Clean up: Delete temporary files so the server's hard drive doesn't fill up
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
