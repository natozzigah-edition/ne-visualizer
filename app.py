from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import tempfile
import json
import subprocess
import uuid

app = Flask(__name__)
# CORS allows your frontend to talk to this backend
CORS(app)

# Use the server's temporary folder to hold finished videos
TEMP_DIR = tempfile.gettempdir()

@app.route('/api/render', methods=['POST'])
def render_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video provided"}), 400

    video_file = request.files['video']
    settings = json.loads(request.form.get('settings', '{}'))

    # Create unique file names so multiple users don't overwrite each other
    input_filename = f"input_{uuid.uuid4().hex}.mp4"
    output_filename = f"ne_visualizer_{uuid.uuid4().hex}.mp4"
    
    input_path = os.path.join(TEMP_DIR, input_filename)
    output_path = os.path.join(TEMP_DIR, output_filename)
    
    video_file.save(input_path)

    try:
        v_settings = settings.get('video', {})
        
        video_filters = []
        if v_settings.get('flip'):
            video_filters.append('hflip')
            
        brightness = (v_settings.get('brightness', 100) - 100) / 100.0
        video_filters.append(f'eq=brightness={brightness}')
        
        if v_settings.get('grayscale') == 100:
            video_filters.append('hue=s=0')
            
        v_filter_str = ','.join(video_filters) if video_filters else 'null'

        command = [
            'ffmpeg', '-y', '-i', input_path,
            '-filter_complex', 
            f"[0:v]{v_filter_str}[vid];"                 
            f"[0:a]showwaves=s=1280x200:mode=cline:colors=white[vis];" 
            f"[vid][vis]overlay=0:H-h[out]",             
            '-map', '[out]', '-map', '0:a',              
            '-c:v', 'libx264', '-preset', 'fast',        
            '-c:a', 'aac',                               
            output_path
        ]

        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Send a JSON link back to the phone instead of the giant file
        return jsonify({"download_url": f"/download/{output_filename}"})

    except subprocess.CalledProcessError as e:
        print(f"FFmpeg Error: {e.stderr.decode()}")
        return jsonify({"error": "Failed to process video"}), 500
    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        # Delete the input file to save space, but leave the output file so the user can download it!
        if os.path.exists(input_path):
            os.remove(input_path)

# New endpoint just for downloading the finished files
@app.route('/download/<filename>')
def download_file(filename):
    path = os.path.join(TEMP_DIR, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True, download_name="ne_visualizer.mp4")
    return "File not found or expired.", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
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
