import os
import json
import logging
import time
from typing import Dict, Any, Optional
import requests
from azure.core.credentials import AzureKeyCredential

def get_content_understanding_client():
    """Initialize Azure Content Understanding client"""
    endpoint = os.environ["CONTENT_UNDERSTANDING_ENDPOINT"]  # e.g., https://myresource.cognitiveservices.azure.com
    key = os.environ["CONTENT_UNDERSTANDING_KEY"]
    return {
        "endpoint": endpoint,
        "key": key,
        "headers": {
            "Ocp-Apim-Subscription-Key": key,
            "Content-Type": "application/json"
        }
    }

def analyze_video_with_content_understanding(video_url: Optional[str] = None, video_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze video using Azure Content Understanding API
    Returns insights about facial expressions, emotions, and visual content
    """
    client_config = get_content_understanding_client()
    
    # Create analyzer configuration for facial analysis
    analyzer_config = {
        "kind": "CustomDocumentAnalyzer",
        "apiVersion": "2024-07-31-preview",
        "enableFace": True,  # Enable face grouping and identification
        "disableFaceBlurring": True,  # Enable face description
        "segmentationMode": "auto",  # Automatic segmentation
        "fieldSchema": {
            "description": "Extract facial expressions and emotional cues for presentation feedback",
            "fields": {
                "emotionDescription": {
                    "type": "string",
                    "method": "generate",
                    "description": "Description of the emotional state and facial expressions of the presenter"
                },
                "confidenceLevel": {
                    "type": "string", 
                    "method": "classify",
                    "description": "Overall confidence level of the presenter",
                    "enum": ["Low", "Medium", "High"]
                },
                "engagementScore": {
                    "type": "string",
                    "method": "generate", 
                    "description": "Assessment of visual engagement through facial expressions and body language"
                },
                "presentationQuality": {
                    "type": "string",
                    "method": "generate",
                    "description": "Overall assessment of presentation delivery based on visual cues"
                }
            }
        },
        "returnDetails": True
    }
    
    # Prepare the request payload
    if video_url:
        payload = {
            "urlSource": video_url,
            "base64Source": None,
            "analyzer": analyzer_config
        }
    else:
        raise NotImplementedError("File upload not implemented yet - use video URL")
    
    # Submit analysis job to Content Understanding
    submit_url = f"{client_config['endpoint']}/documentintelligence/documentAnalyzers/prebuilt-videoAnalyzer:analyze"
    
    response = requests.post(
        submit_url,
        headers=client_config['headers'],
        json=payload,
        params={"api-version": "2024-07-31-preview"}
    )
    
    if response.status_code not in [200, 202]:
        raise Exception(f"Failed to submit analysis: {response.status_code} - {response.text}")
    
    # Get operation location for polling
    operation_location = response.headers.get('Operation-Location')
    if not operation_location:
        # For synchronous responses, return immediately
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("No operation location returned for async operation")
    
    # Poll for results (async operation)
    max_wait_time = 600  # 10 minutes for video processing
    poll_interval = 15   # 15 seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        status_response = requests.get(
            operation_location,
            headers={"Ocp-Apim-Subscription-Key": client_config['key']}
        )
        
        if status_response.status_code == 200:
            result = status_response.json()
            status = result.get('status', '').lower()
            
            if status == 'succeeded':
                return result.get('analyzeResult', {})
            elif status == 'failed':
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                raise Exception(f"Analysis failed: {error_msg}")
            elif status in ['running', 'notstarted']:
                logging.info(f"Analysis status: {status}")
            else:
                logging.warning(f"Unknown status: {status}")
        
        time.sleep(poll_interval)
    
    raise Exception("Analysis timed out after 10 minutes")

def check_analysis_status(job_id: str) -> Dict[str, Any]:
    """Check the status of an ongoing analysis job"""
    client_config = get_content_understanding_client()
    
    # The job_id should be the full operation URL or just the operation ID
    if job_id.startswith('http'):
        status_url = job_id
    else:
        status_url = f"{client_config['endpoint']}/documentintelligence/documentAnalyzers/prebuilt-videoAnalyzer/analyzeResults/{job_id}"
    
    response = requests.get(
        status_url,
        headers={"Ocp-Apim-Subscription-Key": client_config['key']},
        params={"api-version": "2024-07-31-preview"}
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to get status: {response.status_code} - {response.text}")

def generate_presentation_insights(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process Content Understanding results into structured insights for presentation feedback
    """
    insights = {
        "facial_analysis": {
            "faces_detected": 0,
            "face_groupings": [],
            "dominant_emotions": [],
            "facial_expressions": {
                "smile_percentage": 0,
                "neutral_percentage": 0,
                "engaged_percentage": 0
            }
        },
        "visual_sentiment": {
            "overall_tone": "neutral",
            "confidence_indicators": [],
            "energy_level": "medium",
            "segments": []
        },
        "presentation_quality": {
            "visual_engagement": 0,
            "professional_appearance": True,
            "consistency": "good"
        },
        "content_analysis": {
            "transcript": "",
            "key_moments": [],
            "segments": []
        },
        "recommendations": []
    }
    
    # Process Content Understanding results
    if 'documents' in analysis_result:
        for document in analysis_result['documents']:
            # Process custom fields we defined
            fields = document.get('fields', {})
            
            if 'emotionDescription' in fields:
                emotion_desc = fields['emotionDescription'].get('valueString', '')
                insights['visual_sentiment']['segments'].append({
                    "description": emotion_desc,
                    "confidence": fields['emotionDescription'].get('confidence', 0)
                })
            
            if 'confidenceLevel' in fields:
                confidence = fields['confidenceLevel'].get('valueString', 'Medium')
                insights['visual_sentiment']['confidence_indicators'].append(confidence)
            
            if 'engagementScore' in fields:
                engagement_desc = fields['engagementScore'].get('valueString', '')
                insights['presentation_quality']['visual_engagement'] = extract_score_from_text(engagement_desc)
            
            if 'presentationQuality' in fields:
                quality_desc = fields['presentationQuality'].get('valueString', '')
                insights['content_analysis']['segments'].append({
                    "quality_assessment": quality_desc,
                    "confidence": fields['presentationQuality'].get('confidence', 0)
                })
    
    # Process Content Extraction results (faces, transcript, etc.)
    content_extraction = analysis_result.get('contentExtraction', {})
    
    # Face data processing
    if 'faceGroupings' in content_extraction:
        face_data = content_extraction['faceGroupings']
        insights['facial_analysis'] = process_face_groupings(face_data)
    
    # Transcript processing
    if 'transcript' in content_extraction:
        insights['content_analysis']['transcript'] = content_extraction['transcript']
    
    # Key frames processing
    if 'keyFrames' in content_extraction:
        insights['content_analysis']['key_moments'] = process_key_frames(content_extraction['keyFrames'])
    
    # Generate overall sentiment
    insights['visual_sentiment']['overall_tone'] = determine_overall_sentiment(insights)
    
    # Generate recommendations based on analysis
    insights['recommendations'] = generate_recommendations(insights)
    
    return insights

def extract_score_from_text(text: str) -> int:
    """Extract a numerical score from descriptive text"""
    text_lower = text.lower()
    if any(word in text_lower for word in ['excellent', 'outstanding', 'very high', 'great']):
        return 90
    elif any(word in text_lower for word in ['good', 'strong', 'high', 'positive']):
        return 75
    elif any(word in text_lower for word in ['average', 'moderate', 'medium', 'okay']):
        return 60
    elif any(word in text_lower for word in ['below', 'low', 'weak', 'poor']):
        return 40
    else:
        return 50

def process_face_groupings(face_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process face grouping data from Content Understanding"""
    facial_insights = {
        "faces_detected": len(face_data.get('groups', [])),
        "face_groupings": [],
        "dominant_emotions": [],
        "facial_expressions": {
            "smile_percentage": 0,
            "neutral_percentage": 0,
            "engaged_percentage": 0
        }
    }
    
    total_instances = 0
    emotion_counts = {}
    
    for group in face_data.get('groups', []):
        group_info = {
            "group_id": group.get('id', ''),
            "instances": len(group.get('instances', [])),
            "representative_face": group.get('representativeFace', {})
        }
        facial_insights['face_groupings'].append(group_info)
        
        # Process instances for emotion analysis
        for instance in group.get('instances', []):
            total_instances += 1
            # Note: Actual emotion data would come from field extraction
            # This is a placeholder for processing face instance data
    
    return facial_insights

def process_key_frames(key_frames: list) -> list:
    """Process key frames to identify important moments"""
    key_moments = []
    
    for frame in key_frames:
        moment = {
            "timestamp": frame.get('timestamp', ''),
            "description": frame.get('description', ''),
            "confidence": frame.get('confidence', 0)
        }
        key_moments.append(moment)
    
    return key_moments

def determine_overall_sentiment(insights: Dict[str, Any]) -> str:
    """Determine overall sentiment from all analysis components"""
    confidence_indicators = insights['visual_sentiment']['confidence_indicators']
    engagement_score = insights['presentation_quality']['visual_engagement']
    
    if engagement_score > 80 and any('High' in str(indicator) for indicator in confidence_indicators):
        return 'very_positive'
    elif engagement_score > 60:
        return 'positive'
    elif engagement_score > 40:
        return 'neutral'
    else:
        return 'needs_improvement'

def generate_recommendations(insights: Dict[str, Any]) -> list:
    """Generate actionable recommendations based on Content Understanding analysis"""
    recommendations = []
    
    # Visual engagement recommendations
    engagement_score = insights['presentation_quality']['visual_engagement']
    if engagement_score < 60:
        recommendations.append({
            "category": "visual_engagement",
            "suggestion": "Work on maintaining more consistent visual presence and energy throughout the presentation",
            "priority": "high",
            "score_impact": "Could improve overall score by 15-20 points"
        })
    elif engagement_score < 80:
        recommendations.append({
            "category": "visual_engagement", 
            "suggestion": "Good visual engagement! Consider adding more dynamic gestures and facial expressions",
            "priority": "medium",
            "score_impact": "Could improve overall score by 5-10 points"
        })
    
    # Confidence level recommendations
    confidence_indicators = insights['visual_sentiment']['confidence_indicators']
    if any('Low' in str(indicator) for indicator in confidence_indicators):
        recommendations.append({
            "category": "confidence",
            "suggestion": "Focus on projecting more confidence through posture, eye contact, and facial expressions",
            "priority": "high",
            "score_impact": "Critical for presentation effectiveness"
        })
    
    # Face detection recommendations
    faces_detected = insights['facial_analysis']['faces_detected']
    if faces_detected == 0:
        recommendations.append({
            "category": "visibility",
            "suggestion": "Ensure you are clearly visible in the camera frame throughout the presentation",
            "priority": "critical",
            "score_impact": "Essential for effective visual communication"
        })
    elif faces_detected > 1:
        recommendations.append({
            "category": "focus",
            "suggestion": "Consider minimizing distractions by ensuring only the presenter is visible in frame",
            "priority": "medium",
            "score_impact": "Helps maintain audience focus"
        })
    
    # Overall sentiment recommendations
    overall_tone = insights['visual_sentiment']['overall_tone']
    if overall_tone == 'needs_improvement':
        recommendations.append({
            "category": "overall_presence",
            "suggestion": "Focus on improving overall presentation energy and confidence. Practice with video recording to see yourself from the audience perspective.",
            "priority": "high",
            "score_impact": "Fundamental for presentation success"
        })
    elif overall_tone == 'positive':
        recommendations.append({
            "category": "overall_presence",
            "suggestion": "Strong presentation presence! Consider varying your delivery style to maintain audience engagement.",
            "priority": "low",
            "score_impact": "Fine-tuning for excellence"
        })
    
    return recommendations
