import cv2
import numpy as np
import imagehash
from PIL import Image
import pywt
from skimage.metrics import structural_similarity as ssim
from scenedetect import detect, ContentDetector
from sklearn.metrics.pairwise import cosine_similarity
from skimage.feature import hog
from tensorflow.keras.applications import VGG16
from tensorflow.keras.applications.vgg16 import preprocess_input
from tensorflow.keras.preprocessing import image
import tensorflow as tf
from tqdm import tqdm
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

video1 = "video1.mp4"
video2 = "video2.mp4"

def extract_frames(video_path, interval=30, max_frames=15):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open {video_path}")
        return None

    frames = []
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    for i in range(0, min(total_frames, max_frames * interval), interval):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)) 

    cap.release()
    return frames if frames else None

video_frames1=extract_frames(video1)
video_frames2=extract_frames(video2)

def calculate_hash(video_path, algorithm):
    frames = video_frames1 if video_path == video1 else video_frames2
    if frames is None:
        return None
    return [algorithm(Image.fromarray(frame)) for frame in frames]

def similarity_using_hash(video1, video2, algorithm, description):
    print("Finding similarity using hashing algorithms ...")
    
    with tqdm(total=2, desc=description) as pbar:
        hashes1 = calculate_hash(video1, algorithm)
        pbar.update(1)
        hashes2 = calculate_hash(video2, algorithm)
        pbar.update(1)

    if hashes1 is None or hashes2 is None:
        return None

    total_bits = hashes1[0].hash.size
    distances = [h1 - h2 for h1, h2 in zip(hashes1, hashes2)]
    avg_distance = np.mean(distances)

    similarity_percentage = (1 - avg_distance / total_bits) * 100
    return similarity_percentage

def calculate_kp_des(video_path, interval=30, max_frames=15):
    sift = cv2.SIFT_create()
    frames = video_frames1 if video_path == video1 else video_frames2

    if frames is None:
        return None

    keypoints_descriptors = []
    for frame in frames:
        kp, des = sift.detectAndCompute(frame, None)
        if des is not None:
            keypoints_descriptors.append((kp, des))

    return keypoints_descriptors

# def similarity_using_sift(video1, video2, interval=30, max_frames=15):
#     print("Finding similarity using SIFT ...")
#     data1 = calculate_kp_des(video1, interval, max_frames)
#     data2 = calculate_kp_des(video2, interval, max_frames)

#     if not data1 or not data2:
#         return 0

#     min_frame_count = min(len(data1), len(data2))
#     bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
#     similarities = []

#     for i in tqdm(range(min_frame_count), desc="Computing SIFT Similarity"):
#         kp1, des1 = data1[i]
#         kp2, des2 = data2[i]

#         if des1 is None or des2 is None or len(des1) == 0 or len(des2) == 0:
#             continue

#         matches = bf.match(des1, des2)
#         max_dist = max(m.distance for m in matches) if matches else 1
#         good_matches = [m for m in matches if m.distance < 0.75 * max_dist]

#         max_keypoints = max(len(kp1), len(kp2), 1)
#         similarities.append((len(good_matches) / max_keypoints) * 100)

#     return np.mean(similarities) if similarities else 0

# def similarity_using_orb(video1, video2, interval=30, max_frames=15):
#     print("Finding similarity using ORB ...")
#     data1 = calculate_kp_des(video1, interval, max_frames)
#     data2 = calculate_kp_des(video2, interval, max_frames)

#     if not data1 or not data2:
#         return 0

#     min_frame_count = min(len(data1), len(data2))
#     bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
#     similarities = []

#     for i in tqdm(range(min_frame_count), desc="Computing ORB Similarity"):
#         kp1, des1 = data1[i]
#         kp2, des2 = data2[i]

#         if des1 is None or des2 is None or len(des1) == 0 or len(des2) == 0:
#             continue

#         matches = bf.match(des1.astype(np.uint8), des2.astype(np.uint8))
#         good_matches = sorted(matches, key=lambda x: x.distance)[:int(len(matches) * 0.75)]

#         max_keypoints = max(len(kp1), len(kp2), 1)
#         similarities.append((len(good_matches) / max_keypoints) * 100)

#     return np.mean(similarities) if similarities else 0

# def fourier_mellin_transform(image):
#     f = np.fft.fft2(image)
#     fshift = np.fft.fftshift(f)
#     magnitude_spectrum = np.abs(fshift)
#     return np.log1p(magnitude_spectrum)

# def calculate_fmt_signatures(video_path, interval=5, max_frames=15):
#     frames = video_frames1 if video_path == video1 else video_frames2
#     if not frames:
#         return []

#     return [fourier_mellin_transform(frame) for frame in frames]

# def similarity_using_fmt_signatures(video1, video2, interval=5, max_frames=15):
#     print("Computing Fourier-Mellin Transform Similarity...")
#     sig1 = calculate_fmt_signatures(video1, interval, max_frames)
#     sig2 = calculate_fmt_signatures(video2, interval, max_frames)

#     if not sig1 or not sig2:
#         return 0

#     min_frames = min(len(sig1), len(sig2))
#     similarities = []

#     for i in range(min_frames):
#         fmt1, fmt2 = sig1[i], sig2[i]
#         diff = np.linalg.norm(fmt1 - fmt2)
#         max_val = np.max(fmt1) if np.max(fmt1) != 0 else 1
#         similarities.append(np.exp(-diff / (np.max(fmt1) + 1e-8)) * 100)

    # return np.mean(similarities) if similarities else 0

def calculate_color_histogram(video_path, interval=30, max_frames=15):
    frames = video_frames1 if video_path == video1 else video_frames2
    if frames is None:
        return None

    histograms = []
    for frame in frames:
        hist = cv2.calcHist([frame], [0], None, [256], [0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        histograms.append(hist)

    return histograms if histograms else None

def similarity_using_color_histogram(video1, video2):
    histograms1 = calculate_color_histogram(video1)
    histograms2 = calculate_color_histogram(video2)

    if histograms1 is None or histograms2 is None:
        return None

    min_frame_count = min(len(histograms1), len(histograms2))
    hist_similarities = []

    with tqdm(total=min_frame_count, desc="Computing Color Histogram Similarity") as pbar:
        for i in range(min_frame_count):
            similarity = cv2.compareHist(histograms1[i], histograms2[i], cv2.HISTCMP_CORREL) * 100
            hist_similarities.append(similarity)
            pbar.update(1)

    return np.mean(hist_similarities) if hist_similarities else 0

def calculate_wavelet_transform(video_path, interval=30, max_frames=15):
    frames = video_frames1 if video_path == video1 else video_frames2
    if frames is None:
        return None

    wavelet_features = []
    for frame in frames:
        coeffs = pywt.dwt2(frame, 'haar')
        wavelet_features.append(np.mean(coeffs[0]))

    return wavelet_features if wavelet_features else None

def similarity_using_wavelet_transform(video1, video2):
    features1 = calculate_wavelet_transform(video1)
    features2 = calculate_wavelet_transform(video2)

    if features1 is None or features2 is None:
        return None

    min_frame_count = min(len(features1), len(features2))
    similarities = []

    with tqdm(total=min_frame_count, desc="Computing Wavelet Transform Similarity") as pbar:
        for i in range(min_frame_count):
            diff = abs(features1[i] - features2[i])
            similarity = max(0, 100 - diff) 
            similarities.append(similarity)
            pbar.update(1)

    return np.mean(similarities) if similarities else 0

def calculate_motion_vectors(video_path, interval=30, max_frames=15):
    frames = video_frames1 if video_path == video1 else video_frames2
    if frames is None or len(frames) < 2:
        return None

    flow_values = []
    for i in range(len(frames) - 1):
        flow = cv2.calcOpticalFlowFarneback(frames[i], frames[i + 1], None, 0.5, 3, 15, 3, 5, 1.2, 0)
        flow_values.append(np.mean(flow))

    return flow_values if flow_values else None

def similarity_using_motion_vectors(video1, video2):
    flow1 = calculate_motion_vectors(video1)
    flow2 = calculate_motion_vectors(video2)

    if flow1 is None or flow2 is None:
        return None

    min_frame_count = min(len(flow1), len(flow2))
    similarities = []

    with tqdm(total=min_frame_count, desc="Computing Optical Flow Similarity") as pbar:
        for i in range(min_frame_count):
            diff = abs(flow1[i] - flow2[i])
            similarity = max(0, 100 - diff)  
            similarities.append(similarity)
            pbar.update(1)

    return np.mean(similarities) if similarities else 0

# def calculate_scenes(video_path, threshold=30.0):
#     """Detects scenes in a video using a given threshold."""
#     return len(detect(video_path, ContentDetector(threshold=threshold)))

# def similarity_using_scene(video1, video2, threshold=20.0):
#     """Calculates scene-based similarity between two videos."""
#     scenes1 = calculate_scenes(video1, threshold)
#     scenes2 = calculate_scenes(video2, threshold)
    
#     if scenes1 == 0 and scenes2 == 0:
#         return 100  # Both have no scenes, assume identical
#     elif scenes1 == 0 or scenes2 == 0:
#         return 0  # One video has no scenes, assume dissimilar
    
#     similarity = (1 - abs(scenes1 - scenes2) / max(scenes1, scenes2)) * 100
#     return similarity

def calculate_cnn_fingerprints(video_path, interval=30, max_frames=15):
    model = VGG16(weights='imagenet', include_top=False)
    frames = video_frames1 if video_path == video1 else video_frames2
    if frames is None:
        return None

    fingerprints = []
    for frame in frames:
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  
        img = cv2.resize(img, (224, 224))  
        img = image.img_to_array(img)
        img = np.expand_dims(img, axis=0)
        img = preprocess_input(img)  
        features = model.predict(img)  
        fingerprints.append(np.mean(features))  

    return fingerprints

def similarity_cnn_fingerprint(video1, video2, interval=30, max_frames=15):
    print("Computing CNN Fingerprinting Similarity...")

    fingerprints1 = calculate_cnn_fingerprints(video1, interval, max_frames)
    fingerprints2 = calculate_cnn_fingerprints(video2, interval, max_frames)

    if fingerprints1 is None or fingerprints2 is None:
        return 0  # Return 0 if fingerprint extraction fails

    min_frames = min(len(fingerprints1), len(fingerprints2))
    similarities = []

    for i in range(min_frames):
        f1, f2 = fingerprints1[i], fingerprints2[i]
        similarity = (1 - abs(f1 - f2) / max(f1, f2)) * 100
        similarities.append(similarity)

    return np.mean(similarities) if similarities else 0  # Return average similarity

# def calculate_motion_vectors(video_path, interval=5, max_frames=15):
#     frames = video_frames1 if video_path == video1 else video_frames2
#     if frames is None:
#         return None

#     motion_vectors = []
#     for i in range(len(frames) - 1):
#         prev_frame = frames[i]
#         next_frame = frames[i + 1]

#         flow = cv2.calcOpticalFlowFarneback(prev_frame, next_frame, None, 
#                                             0.5, 3, 15, 3, 5, 1.2, 0)
#         motion_vectors.append(np.mean(np.abs(flow)))  # Store motion magnitude

#     return motion_vectors

# def similarity_using_motion_vectors(video1, video2, interval=5, max_frames=15):
#     """ Computes similarity between two videos using motion vectors. """
#     print("Computing Motion Vector Similarity...")

#     motion1 = calculate_motion_vectors(video1, interval, max_frames)
#     motion2 = calculate_motion_vectors(video2, interval, max_frames)

#     if motion1 is None or motion2 is None:
#         return 0  # Return 0 if motion extraction fails

#     min_frames = min(len(motion1), len(motion2))
#     similarities = []

#     for i in range(min_frames):
#         m1, m2 = motion1[i], motion2[i]
#         similarity = (1 - abs(m1 - m2) / max(m1, m2)) * 100
#         similarities.append(similarity)

#     return np.mean(similarities) if similarities else 0  # Return average similarity

def extract_spatio_temporal_features(video_path: str, num_frames: int = 10) -> np.ndarray:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_indices = np.linspace(0, total_frames-1, num_frames, dtype=int)
    video_features = []
    
    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (128, 128))
        hog_features = hog(resized, 
                           orientations=9, 
                           pixels_per_cell=(16, 16),
                           cells_per_block=(2, 2),
                           block_norm='L2-Hys')
        
        video_features.append(hog_features)
    
    cap.release()
    return np.concatenate(video_features)

def similarity_using_spatio(video1_path: str, video2_path: str) -> float:
    try:
        features1 = extract_spatio_temporal_features(video1_path)
        features2 = extract_spatio_temporal_features(video2_path)
        
        features1 = features1.reshape(1, -1)
        features2 = features2.reshape(1, -1)
        
        similarity = cosine_similarity(features1, features2)[0][0]

        similarity_percentage = similarity * 100
        
        return similarity_percentage
    
    except Exception as e:
        print(f"Error calculating video similarity: {e}")
        return 0.0

# print(f"pHash Similarity: {similarity_using_hash(video1,video2,imagehash.phash,"Computing perceptual hashes"):.2f}%")
# print(f"dHash Similarity: {similarity_using_hash(video1,video2,imagehash.dhash,"Computing difference hashes"):.2f}%")
# print(f"aHash Similarity: {similarity_using_hash(video1,video2,imagehash.average_hash,"Computing average hashes"):.2f}%")
# print(f"BMVHash Similarity: {similarity_using_hash(video1, video2, imagehash.whash, 'Computing block mean value hashes'):.2f}%")
# print(f"SIFT Similarity: {similarity_using_sift(video1, video2):.2f}%")
# print(f"ORB Similarity: {similarity_using_orb(video1, video2):.2f}%")
# print(f"FMT Similarity: {similarity_using_fmt_signatures(video1, video2):.2f}%")
# print(f"Color Histogram Similarity: {similarity_using_color_histogram(video1, video2):.2f}%")
# print(f"Wavelet Transform Similarity: {similarity_using_wavelet_transform(video1, video2):.2f}%")
# print(f"Motion Vector Similarity: {similarity_using_motion_vectors(video1, video2):.2f}%")
# print(f"Scene Similarity: {similarity_using_scene(video1, video2):.2f}%")
# print(f"CNN Fingerprinting Similarity: {similarity_cnn_fingerprint(video1, video2):.2f}%")
# print(f"Spatio Similarity: {calculate_video_similarity(video1, video2):.2f}%")

def average_similarity(video1, video2):
    pHash_sim = similarity_using_hash(video1, video2, imagehash.phash, "Computing perceptual hashes")
    print(f"pHash Similarity: {pHash_sim:.2f}%")

    dHash_sim = similarity_using_hash(video1, video2, imagehash.dhash, "Computing difference hashes")
    print(f"dHash Similarity: {dHash_sim:.2f}%")

    aHash_sim = similarity_using_hash(video1, video2, imagehash.average_hash, "Computing average hashes")
    print(f"aHash Similarity: {aHash_sim:.2f}%")

    BMVHash_sim = similarity_using_hash(video1, video2, imagehash.whash, "Computing block mean value hashes")
    print(f"BMVHash Similarity: {BMVHash_sim:.2f}%")

    # SIFT_sim = similarity_using_sift(video1, video2)
    # print(f"SIFT Similarity: {SIFT_sim:.2f}%")

    # ORB_sim = similarity_using_orb(video1, video2)
    # print(f"ORB Similarity: {ORB_sim:.2f}%")

    # FMT_sim = similarity_using_fmt_signatures(video1, video2)
    # print(f"FMT Similarity: {FMT_sim:.2f}%")

    ColorHist_sim = similarity_using_color_histogram(video1, video2)
    print(f"Color Histogram Similarity: {ColorHist_sim:.2f}%")

    Wavelet_sim = similarity_using_wavelet_transform(video1, video2)
    print(f"Wavelet Transform Similarity: {Wavelet_sim:.2f}%")

    MotionVec_sim = similarity_using_motion_vectors(video1, video2)
    print(f"Motion Vector Similarity: {MotionVec_sim:.2f}%")

    # Scene_sim = similarity_using_scene(video1, video2)
    # print(f"Scene Similarity: {Scene_sim:.2f}%")

    CNN_sim = similarity_cnn_fingerprint(video1, video2)
    print(f"CNN Fingerprinting Similarity: {CNN_sim:.2f}%")

    Spatio_sim = similarity_using_spatio(video1, video2)
    print(f"Spatio Similarity: {Spatio_sim:.2f}%")

    # similarities = [
    #     pHash_sim, dHash_sim, aHash_sim, BMVHash_sim, SIFT_sim, ORB_sim, 
    #     FMT_sim, ColorHist_sim, Wavelet_sim, MotionVec_sim, Scene_sim, CNN_sim, Spatio_sim
    # ]

    similarities = [
        pHash_sim, dHash_sim, aHash_sim, BMVHash_sim, ColorHist_sim, Wavelet_sim, MotionVec_sim, CNN_sim, Spatio_sim
    ]

    avg_sim = sum(similarities) / len(similarities)
    print(f"Average Similarity: {avg_sim:.2f}%")

    return avg_sim

average_similarity_percentage = average_similarity(video1, video2)

