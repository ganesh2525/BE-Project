import cv2
import numpy as np
from scipy import signal
from scipy.signal.windows import gaussian
from scipy.fftpack import dct
from scipy.signal import convolve

fingerprint_db = {}

video_content_map = {
    "v1.mp4": "beach",
    "v1-noise.mp4": "beach",
    "v1-brightness.mp4": "beach",
    "v1-contrast.mp4": "beach",
    "v1-rotate.mp4": "beach",
    "v1-shift.mp4": "beach",
    "v1-frame_loss.mp4": "beach",
    "v1-shift-rotate.mp4": "beach",
    "v1-contrast-frame_loss.mp4": "beach",
    "v1-trim.mp4": "beach"
}

def classify_video(video_path):
    """Returns a category for the video (ML model placeholder)."""
    return video_content_map.get(video_path, "unknown")

def preprocess_video(video_path, target_width, target_height, target_fps):
    cap = cv2.VideoCapture(video_path)
    orig_fps = cap.get(cv2.CAP_PROP_FPS)
    spatial_kernel = cv2.getGaussianKernel(5, 1.0)
    temporal_kernel = gaussian(5, std=1.0).reshape(-1, 1, 1)
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
    filtered_frames = convolve(frames, temporal_kernel, mode='same')
    target_frame_count = int(len(frames) * target_fps / orig_fps)
    resampled_frames = signal.resample(filtered_frames, target_frame_count, axis=0)
    return resampled_frames

def segment_video(frames, segment_length):
    total_frames = len(frames)
    segments = [frames[i:i + segment_length] for i in range(0, total_frames - segment_length + 1, segment_length)]
    return segments

def generate_tiri(segment, beta=0.6):
    weights = np.exp(-beta * np.arange(len(segment)))
    weights = weights / np.sum(weights)
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
    frames = preprocess_video(video_path, config['width'], config['height'], config['fps'])
    segments = segment_video(frames, config['segment_length'])
    hashes = []
    for segment in segments:
        tiri = generate_tiri(segment, config['beta'])
        features = extract_features(tiri, config['block_size'])
        hashes.append(generate_hash(features))
    return hashes

def compare_hashes(hash1, hash2):
    if len(hash1) != len(hash2):
        raise ValueError("Hash lengths must match")
    return np.sum(hash1 != hash2) / len(hash1)

def process_videos(video_files, hash_database, config):
    category_hashes = {}
    for video_path in video_files:
        category = classify_video(video_path)
        print(f"Classified {video_path} as {category}")
        video_hashes = compute_video_hash(video_path, config)
        strike_given = False
        if category in category_hashes:
            for db_hashes in category_hashes[category]:
                for db_hash in db_hashes:
                    for video_hash in video_hashes:
                        if compare_hashes(video_hash, db_hash) < 0.24:
                            print(f"Copyright strike issued for {video_path}","\n")
                            strike_given = True
                            break
                    if strike_given:
                        break
                if strike_given:
                    break
        if not strike_given:
            if category not in category_hashes:
                category_hashes[category] = []
            category_hashes[category].append(video_hashes)

if __name__ == "_main_":
    video_files = [
        "v1.mp4", "v1-trim.mp4","v1-brightness.mp4","v1-contrast.mp4",
        "v1-contrast-frame_loss.mp4","v1-frame_loss.mp4","v1-shift-rotate.mp4",
        "v1-shift.mp4"
    ]
    hash_database = []
    config = {
        'width': 176,
        'height': 144,
        'fps': 4,
        'segment_length': 8,
        'beta': 0.6,
        'block_size': 8
    }
    process_videos(video_files, hash_database, config)
    print("Hashes computed and stored in database.")