import os
import cv2
import gdown
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.json_util import dumps
import numpy as np
from scipy import signal
from scipy.signal.windows import gaussian
from scipy.fftpack import dct
from scipy.signal import convolve
import smtplib
from email.mime.text import MIMEText
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb+srv://ganesh_93:ganesh93@mern.kq359yn.mongodb.net")  # change URI if needed
db = client["YouTube"]

# --- Fingerprinting Algorithm Functions (from your code) ---

def download_video_if_needed(video_url):
    if video_url.startswith("https://drive.google.com"):
        file_id = video_url.split("/d/")[1].split("/")[0]
        output_path = f"temp_{file_id}.mp4"
        if not os.path.exists(output_path):
            gdown.download(f"https://drive.google.com/uc?id={file_id}", output_path, quiet=False)
        return output_path
    return video_url

def preprocess_video(video_path, target_width, target_height, target_fps):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Failed to open video: {video_path}")

    orig_fps = cap.get(cv2.CAP_PROP_FPS)
    spatial_kernel = cv2.getGaussianKernel(5, 1.0)
    temporal_kernel = gaussian(5, std=1.0)

    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (target_width, target_height))
        filtered = cv2.filter2D(resized, -1, spatial_kernel)
        frames.append(filtered)
    cap.release()

    frames = np.array(frames)

    if frames.ndim != 3:
        raise ValueError(f"Unexpected frame shape: {frames.shape}")

    filtered_frames = np.copy(frames)
    for i in range(frames.shape[1]):
        for j in range(frames.shape[2]):
            filtered_frames[:, i, j] = np.convolve(
                frames[:, i, j], temporal_kernel / temporal_kernel.sum(), mode='same'
            )

    target_frame_count = int(len(filtered_frames) * target_fps / orig_fps)
    resampled_frames = signal.resample(filtered_frames, target_frame_count, axis=0)
    return resampled_frames


def segment_video(frames, segment_length):
    return [frames[i:i + segment_length] for i in range(0, len(frames) - segment_length + 1, segment_length)]

def generate_tiri(segment, beta=0.6):
    weights = np.exp(-beta * np.arange(len(segment)))
    weights /= np.sum(weights)
    tiri = np.zeros_like(segment[0], dtype=float)
    for i, frame in enumerate(segment):
        tiri += frame * weights[i]
    return np.uint8(np.clip(tiri, 0, 255))

def extract_features(tiri, block_size=8):
    dct_transform = dct(dct(tiri.T, norm='ortho').T, norm='ortho')
    return dct_transform[:block_size, :block_size].flatten()

def generate_hash(features):
    median = np.median(features)
    return (features > median).astype(int)

def compute_video_hash(video_path, config):
    local_path = download_video_if_needed(video_path)
    frames = preprocess_video(local_path, config['width'], config['height'], config['fps'])
    segments = segment_video(frames, config['segment_length'])
    hashes = []
    for segment in segments:
        tiri = generate_tiri(segment, config['beta'])
        features = extract_features(tiri, config['block_size'])
        hashes.append(generate_hash(features))
    return hashes

def compare_hashes(hash1, hash2):
    return np.sum(hash1 != hash2) / len(hash1)

# def send_email_notification(to_email, video_url):
#     msg = MIMEText(f"Your video is similar to one in our database: {video_url}")
#     msg["Subject"] = "Video Similarity Detected"
#     msg["From"] = "ganesh3567lokhande@gmail.com"
#     msg["To"] = to_email

#     # Gmail SMTP
#     with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
#         server.login("ganesh3567lokhande@gmail.com", "vjdy wmsi usaa hyql")
#         server.send_message(msg)

import smtplib
from email.mime.text import MIMEText

def send_email_notification(to_email, video_url):
    body = f"""
Dear User,

It appears that someone has attempted to copy your video content. We found a similar video in our database:

Matched Video URL: {video_url}

Our team is reviewing this matter and will take necessary action shortly.

Regards,  
Copyright Protection Team
"""

    msg = MIMEText(body)
    msg["Subject"] = "Copyright Infringement Detected"
    msg["From"] = "ganesh3567lokhande@gmail.com"
    msg["To"] = to_email

    # Gmail SMTP
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login("ganesh3567lokhande@gmail.com", "vjdy wmsi usaa hyql")
        server.send_message(msg)

# --- Main API Endpoint ---


def progress_tracker(step, total):
    return int((step / total) * 100)

@app.route("/get-similarity", methods=["POST"])
def get_similarity():
    try:
        data = request.get_json()
        video_url = data["video_url"]
        email = data["email"]
        category = data["video_category"]

        config = {
            'width': 176,
            'height': 144,
            'fps': 4,
            'segment_length': 8,
            'beta': 0.6,
            'block_size': 8
        }

        total_steps = 5
        step = 0

        # Step 1: Download video
        local_path = download_video_if_needed(video_url)
        step += 1
        print(f"Downloading video: {progress_tracker(step, total_steps)}%")

        # Step 2: Preprocess
        frames = preprocess_video(local_path, config['width'], config['height'], config['fps'])
        step += 1
        print(f"Preprocessing video: {progress_tracker(step, total_steps)}%")

        # Step 3: Segment & hash
        segments = segment_video(frames, config['segment_length'])
        hashes = []
        for segment in segments:
            tiri = generate_tiri(segment, config['beta'])
            features = extract_features(tiri, config['block_size'])
            hashes.append(generate_hash(features))
        step += 1
        print(f"Segmenting and hashing: {progress_tracker(step, total_steps)}%")

        # Step 4: Compare with DB
        collection = db[category]
        documents = list(collection.find())
        for doc in documents:
            stored_hashes = doc["hash"]
            for h1 in hashes:
                for h2 in stored_hashes:
                    h2 = np.array(h2)
                    if compare_hashes(h1, h2) < 0.24:
                        step += 1
                        print(f"Comparing with database: {progress_tracker(step, total_steps)}%")
                        send_email_notification(doc["email"], video_url)
                        return jsonify({
                            "strike": True,
                        })

        # Step 5: Store new
        collection.insert_one({
            "video_url": video_url,
            "email": email,
            "hash": [h.tolist() for h in hashes]
        })
        step += 1
        print(f"Storing new video: {progress_tracker(step, total_steps)}%")

        return jsonify({
            "strike": False,
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)