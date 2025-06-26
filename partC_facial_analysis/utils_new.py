import os
import json
import logging
import time
import cv2
import tempfile
import requests
from typing import Dict, Any, Optional, List
import numpy as np
from urllib.parse import urlparse

def get_azure_ai_client():
    """Initialize Azure AI Services client"""
    endpoint = os.environ.get("CONTENT_UNDERSTANDING_ENDPOINT")
    key = os.environ.get("CONTENT_UNDERSTANDING_KEY")
    
    if not endpoint or not key:
        raise ValueError("Missing Azure AI Services credentials. Set CONTENT_UNDERSTANDING_ENDPOINT and CONTENT_UNDERSTANDING_KEY environment variables.")
    
    return {
        "endpoint": endpoint,
        "key": key,
        "headers": {
            "Ocp-Apim-Subscription-Key": key,
            "Content-Type": "application/json"
        }
    }

def detect_faces_in_image(image_data: bytes) -> Dict[str, Any]:
    """
    Detect faces in an image using Azure Face API
    Returns face detection results with available attributes
    """
    client_config = get_azure_ai_client()
    
    # Use Face API endpoint for detection
    url = f"{client_config['endpoint']}/face/v1.0/detect"
    
    # Parameters for face detection
    params = {
        'returnFaceId': 'true',
        'returnFaceLandmarks': 'true',
        'returnFaceAttributes': 'age,smile,facialHair,glasses,headPose,accessories,blur,exposure,noise,mask,qualityForRecognition'
    }
    
    headers = {
        "Ocp-Apim-Subscription-Key": client_config['key'],
        "Content-Type": "application/octet-stream"
    }
    
    try:
        response = requests.post(url, params=params, headers=headers, data=image_data, timeout=30)
        
        if response.status_code == 200:
            return {
                "success": True,
                "faces": response.json(),
                "face_count": len(response.json())
            }
        else:
            return {
                "success": False,
                "error": f"Face detection failed: {response.status_code} - {response.text}",
                "face_count": 0
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Exception during face detection: {str(e)}",
            "face_count": 0
        }

def download_video(video_url: str) -> str:
    """Download video to temporary file"""
    try:
        response = requests.get(video_url, stream=True, timeout=60)
        response.raise_for_status()
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        
        for chunk in response.iter_content(chunk_size=8192):
            temp_file.write(chunk)
        
        temp_file.close()
        return temp_file.name
        
    except Exception as e:
        raise Exception(f"Failed to download video: {str(e)}")

def extract_frames_from_video(video_path: str, max_frames: int = 10) -> List[bytes]:
    """Extract frames from video for analysis"""
    frames = []
    
    try:
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise Exception("Failed to open video file")
        
        # Get total frame count and fps
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        
        # Calculate frame intervals
        if total_frames <= max_frames:
            frame_interval = 1
        else:
            frame_interval = total_frames // max_frames
        
        frame_count = 0
        extracted_count = 0
        
        while cap.isOpened() and extracted_count < max_frames:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Extract frame at intervals
            if frame_count % frame_interval == 0:
                # Convert frame to JPEG bytes
                success, buffer = cv2.imencode('.jpg', frame)
                if success:
                    frame_bytes = buffer.tobytes()
                    frames.append(frame_bytes)
                    extracted_count += 1
            
            frame_count += 1
        
        cap.release()
        
        return frames
        
    except Exception as e:
        raise Exception(f"Failed to extract frames: {str(e)}")

def analyze_video_with_face_detection(video_url: Optional[str] = None, video_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze video using Azure Face API
    Downloads video, extracts frames, and analyzes faces in each frame
    """
    
    try:
        # Download video if URL provided
        if video_url:
            print(f"📥 Downloading video from: {video_url}")
            video_path = download_video(video_url)
        elif video_file:
            video_path = video_file
        else:
            return {
                "success": False,
                "error": "No video URL or file provided"
            }
        
        # Extract frames
        print("🎬 Extracting frames from video...")
        frames = extract_frames_from_video(video_path, max_frames=10)
        
        if not frames:
            return {
                "success": False,
                "error": "No frames could be extracted from video"
            }
        
        print(f"📸 Extracted {len(frames)} frames for analysis")
        
        # Analyze each frame
        all_faces = []
        frame_analyses = []
        
        for i, frame_data in enumerate(frames):
            print(f"🔍 Analyzing frame {i+1}/{len(frames)}...")
            
            result = detect_faces_in_image(frame_data)
            
            frame_analysis = {
                "frame_number": i + 1,
                "timestamp": f"{i * 2:.1f}s",  # Approximate timestamp
                "face_detection_success": result["success"],
                "face_count": result["face_count"],
                "faces": result.get("faces", [])
            }
            
            if result["success"]:
                all_faces.extend(result["faces"])
            
            frame_analyses.append(frame_analysis)
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        # Generate insights
        insights = generate_video_insights(frame_analyses, all_faces)
        
        # Clean up temporary file
        if video_url:
            try:
                os.unlink(video_path)
            except:
                pass
        
        return {
            "success": True,
            "insights": insights,
            "frame_analyses": frame_analyses,
            "total_faces_detected": len(all_faces),
            "frames_analyzed": len(frames)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def generate_video_insights(frame_analyses: List[Dict], all_faces: List[Dict]) -> Dict[str, Any]:
    """Generate insights from face detection results"""
    
    if not all_faces:
        return {
            "summary": "No faces detected in video",
            "engagement_level": "Unable to determine",
            "confidence_indicators": [],
            "recommendations": ["Ensure presenter is clearly visible in frame", "Check video quality and lighting"]
        }
    
    # Analyze face attributes
    smiles = []
    ages = []
    head_poses = []
    quality_scores = []
    
    for face in all_faces:
        attrs = face.get("faceAttributes", {})
        
        # Collect smile scores
        if "smile" in attrs:
            smiles.append(attrs["smile"])
        
        # Collect ages
        if "age" in attrs:
            ages.append(attrs["age"])
        
        # Collect head pose data
        if "headPose" in attrs:
            head_poses.append(attrs["headPose"])
        
        # Collect quality scores
        if "qualityForRecognition" in attrs:
            quality = attrs["qualityForRecognition"]
            if quality == "high":
                quality_scores.append(3)
            elif quality == "medium":
                quality_scores.append(2)
            else:
                quality_scores.append(1)
    
    # Calculate metrics
    avg_smile = sum(smiles) / len(smiles) if smiles else 0
    avg_age = sum(ages) / len(ages) if ages else 0
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    
    # Determine engagement level
    if avg_smile > 0.7:
        engagement = "High"
    elif avg_smile > 0.3:
        engagement = "Medium"
    else:
        engagement = "Low"
    
    # Generate recommendations
    recommendations = []
    if avg_smile < 0.5:
        recommendations.append("Consider incorporating more engaging content or humor")
    if avg_quality < 2:
        recommendations.append("Improve video quality and lighting")
    if len(head_poses) > 0:
        # Check for consistent head positioning
        recommendations.append("Maintain consistent eye contact with camera")
    
    return {
        "summary": f"Detected {len(all_faces)} faces across {len(frame_analyses)} frames",
        "engagement_level": engagement,
        "average_smile_score": round(avg_smile, 2),
        "presenter_age_estimate": round(avg_age) if avg_age > 0 else "Not available",
        "video_quality": "High" if avg_quality >= 2.5 else "Medium" if avg_quality >= 1.5 else "Low",
        "confidence_indicators": [
            f"Smile detection confidence: {avg_smile:.1%}",
            f"Face quality: {avg_quality:.1f}/3.0",
            f"Frames with faces: {len([f for f in frame_analyses if f['face_count'] > 0])}/{len(frame_analyses)}"
        ],
        "recommendations": recommendations if recommendations else ["Great presentation! Keep up the good work."]
    }

# For backward compatibility
def analyze_video_with_content_understanding(video_url: Optional[str] = None, video_file: Optional[str] = None) -> Dict[str, Any]:
    """Legacy function name - redirects to new implementation"""
    return analyze_video_with_face_detection(video_url, video_file)
