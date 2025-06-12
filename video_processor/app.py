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
from tqdm import tqdm
from dotenv import load_dotenv
import subprocess
import uuid
load_dotenv()

app = Flask(__name__)
CORS(app)

total_steps = 5
progress_bar = tqdm(total=total_steps, desc="Processing", unit="step")

mongo_uri = os.getenv("MONGO_URI")
mongo_db = os.getenv("MONGO_DB")

client = MongoClient(mongo_uri)  # change URI if needed
db = client[mongo_db]

# --- Fingerprinting Algorithm Functions (from your code) ---

def download_video_if_needed(video_url):
    if video_url.startswith("https://drive.google.com"):
        file_id = video_url.split("/d/")[1].split("/")[0]
        output_path = f"temp_{file_id}.mp4"
        if not os.path.exists(output_path):
            gdown.download(f"https://drive.google.com/uc?id={file_id}", output_path, quiet=False)
        return output_path
    
    # unique_id = uuid.uuid4().hex
    # output_path2 = f"temp_{unique_id}.mp4"
    # subprocess.run(["ffmpeg", "-i", video_url, "-c", "copy", output_path2], check=True)
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

# def compare_hashes(hash1, hash2):
#     return np.sum(hash1 != hash2) / len(hash1)

def compare_hashes(h1, h2):
    len_diff = abs(len(h1) - len(h2))
    if len(h1) < len(h2):
        pad_val = int(np.median(h1))
        h1 = np.pad(h1, (0, len_diff), constant_values=pad_val)
    elif len(h2) < len(h1):
        pad_val = int(np.median(h2))
        h2 = np.pad(h2, (0, len_diff), constant_values=pad_val)
    return np.sum(h1 != h2) / len(h1)

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
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = to_email

    # Gmail SMTP
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
        server.send_message(msg)

# Optional: Try another algorithm if strike is False
# def alternate_compare(video_path1, video_path2):
#     # Basic frame difference comparator for fallback
#     cap1 = cv2.VideoCapture(video_path1)
#     cap2 = cv2.VideoCapture(video_path2)

#     match_count = 0
#     total = 0
#     while True:
#         ret1, frame1 = cap1.read()
#         ret2, frame2 = cap2.read()
#         if not ret1 or not ret2:
#             break
#         gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
#         gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
#         diff = cv2.absdiff(gray1, gray2)
#         score = np.mean(diff)
#         if score < 30:  # threshold
#             match_count += 1
#         total += 1

#     cap1.release()
#     cap2.release()

#     return match_count / total if total > 0 else 1.0

def alternate_compare(video_path1, video_path2, config):
    cap1 = cv2.VideoCapture(video_path1)
    cap2 = cv2.VideoCapture(video_path2)

    match_count = 0
    total = 0
    while True:
        ret1, frame1 = cap1.read()
        ret2, frame2 = cap2.read()
        if not ret1 or not ret2:
            break

        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

        # Resize both to a common size
        target_size = (config['width'], config['height'])
        gray1 = cv2.resize(gray1, target_size)
        gray2 = cv2.resize(gray2, target_size)

        diff = cv2.absdiff(gray1, gray2)
        score = np.mean(diff)
        if score < 30:
            match_count += 1
        total += 1

    cap1.release()
    cap2.release()

    return match_count / total if total > 0 else 1.0

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
        print("video_url: ",video_url)
        print("email: ",email)
        print("video_category: ",category)

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
        print(f"Downloading video, Progress: {progress_tracker(step, total_steps)}%")
        # progress_bar.update(1)

        # Step 2: Preprocess
        frames = preprocess_video(local_path, config['width'], config['height'], config['fps'])
        step += 1
        print(f"Preprocessing video, Progress: {progress_tracker(step, total_steps)}%")
        # progress_bar.update(1)

        # Step 3: Segment & hash
        segments = segment_video(frames, config['segment_length'])
        hashes = []
        for segment in segments:
            tiri = generate_tiri(segment, config['beta'])
            features = extract_features(tiri, config['block_size'])
            hashes.append(generate_hash(features))
        step += 1
        print(f"Segmenting and hashing, Progress: {progress_tracker(step, total_steps)}%")
        # progress_bar.update(1)

        # Step 4: Compare with DB
        # collection = db[category]
        # documents = list(collection.find())
        # for doc in documents:
        #     stored_hashes = doc["hash"]
        #     for h1 in hashes:
        #         for h2 in stored_hashes:
        #             h2 = np.array(h2)
        #             if compare_hashes(h1, h2) < 0.24:
        #                 step += 1
        #                 print(f"Comparing with database: {progress_tracker(step, total_steps)}%")
        #                 send_email_notification(doc["email"], video_url)
        #                 return jsonify({
        #                     "strike": True,
        #                 })

        collection = db[category]
        documents = list(collection.find())
        for doc in documents:
            if doc.get("email") == email:
                continue
            stored_hashes = doc["hash"]
            for h1 in hashes:
                for h2 in stored_hashes:
                    h2 = np.array(h2)
                    if compare_hashes(h1, h2) < 0.24:
                        step += 1
                        print(f"Comparing with database: {progress_tracker(step, total_steps)}%")
                        send_email_notification(doc["email"], video_url)
                        print("strike : True")
                        return jsonify({
                            "strike": True,
                            "method": "first"
                        })
        # progress_bar.update(1)    

        # Step 5: Store new
        # collection.insert_one({
        #     "video_url": video_url,
        #     "email": email,
        #     "hash": [h.tolist() for h in hashes]
        # })
        # step += 1
        # print(f"Storing new video: {progress_tracker(step, total_steps)}%")

        # return jsonify({
        #     "strike": False,
        # })

        # Step 5: If no match found with primary algo, fallback comparison
        for doc in documents:
            if doc.get("email") == email:
                continue
            other_video_path = download_video_if_needed(doc["video_url"])
            sim_score = alternate_compare(local_path, other_video_path, config)
            if other_video_path.startswith("temp_") and os.path.exists(other_video_path):
                os.remove(other_video_path)
            if sim_score > 0.7:  # You decide threshold
                send_email_notification(doc["email"], video_url)
                print("strike : True")
                return jsonify({
                    "strike": True,
                    "method": "second"
                })
        # progress_bar.update(1)

        # Store new
        collection.insert_one({
            "video_url": video_url,
            "email": email,
            "hash": [h.tolist() for h in hashes]
        })
        step += 1
        print(f"Storing new video, Progress: {progress_tracker(step, total_steps)}%")
        progress_bar.update(1)

        print("strike : False")
        return jsonify({
            "strike": False,
            "method": "none"
        })

    except Exception as e:
        print("Error occurred:", str(e))
        return jsonify({"error": str(e)})
    
    finally:
        if local_path and local_path.startswith("temp_") and os.path.exists(local_path):
            os.remove(local_path)

if __name__ == "__main__":
    app.run(debug=True)