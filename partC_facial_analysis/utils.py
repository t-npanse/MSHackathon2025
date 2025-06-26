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
            },
            # EXPANDED: Temporal emotion tracking
            "emotion_timeline": [],
            "emotion_consistency": {
                "variability_score": 0,
                "most_stable_emotion": "",
                "emotion_transitions": []
            }
        },
        "visual_sentiment": {
            "overall_tone": "neutral",
            "confidence_indicators": [],
            "energy_level": "medium",
            "segments": [],
            # EXPANDED: Detailed emotional patterns
            "emotional_patterns": {
                "opening_confidence": 0,
                "mid_presentation_energy": 0, 
                "closing_impact": 0,
                "stress_indicators": [],
                "engagement_peaks": []
            }
        },
        "presentation_quality": {
            "visual_engagement": 0,
            "professional_appearance": True,
            "consistency": "good",
            # EXPANDED: Detailed quality metrics
            "body_language": {
                "posture_score": 0,
                "gesture_effectiveness": 0,
                "eye_contact_rating": 0
            },
            "delivery_effectiveness": {
                "authenticity_score": 0,
                "charisma_indicators": [],
                "audience_connection": 0
            }
        },
        "content_analysis": {
            "transcript": "",
            "key_moments": [],
            "segments": [],
            # EXPANDED: Content-emotion correlation
            "emotional_content_mapping": {
                "high_energy_topics": [],
                "low_engagement_sections": [],
                "emotional_relevance": []
            }
        },
        # EXPANDED: Comprehensive coaching insights
        "coaching_insights": {
            "personality_style": "",
            "communication_strengths": [],
            "growth_opportunities": [],
            "speaker_archetype": "",
            "recommended_techniques": []
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
    
    # ENHANCED: Analyze emotional patterns for deeper insights
    insights['visual_sentiment']['emotional_patterns'] = analyze_emotional_patterns(insights)
    
    # ENHANCED: Determine speaker archetype for personalized coaching
    insights['coaching_insights']['speaker_archetype'] = determine_speaker_archetype(insights)
    
    # ENHANCED: Generate comprehensive coaching insights
    comprehensive_coaching = generate_comprehensive_coaching_insights(insights)
    insights['coaching_insights'].update(comprehensive_coaching)
    
    # ENHANCED: Generate comprehensive recommendations with coaching depth
    insights['recommendations'] = generate_enhanced_recommendations(insights)
    
    # Add backward compatibility - keep original function too
    insights['basic_recommendations'] = generate_recommendations(insights)
    
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

def generate_enhanced_recommendations(insights: Dict[str, Any]) -> list:
    """Generate comprehensive, actionable recommendations with coaching depth"""
    recommendations = []
    
    # Get key metrics
    engagement_score = insights['presentation_quality']['visual_engagement']
    emotion_timeline = insights['facial_analysis']['emotion_timeline']
    emotional_patterns = insights['visual_sentiment']['emotional_patterns']
    
    # ENGAGEMENT-BASED RECOMMENDATIONS
    if engagement_score > 90:
        recommendations.append({
            "category": "excellence",
            "suggestion": "Outstanding visual engagement! You're a natural presenter. Consider mentoring others or speaking at larger events.",
            "priority": "celebration",
            "score_impact": "Maintain this excellence",
            "coaching_depth": "advanced",
            "next_steps": ["Record yourself for self-analysis", "Seek speaking opportunities", "Develop signature presentation style"]
        })
    elif engagement_score > 80:
        recommendations.append({
            "category": "visual_engagement",
            "suggestion": "Strong visual presence! To reach the next level, focus on varying your facial expressions during key transitions and using more purposeful gestures.",
            "priority": "medium",
            "score_impact": "Could elevate score to 90+",
            "coaching_depth": "intermediate",
            "next_steps": ["Practice with mirror", "Record practice sessions", "Work on gesture timing"]
        })
    elif engagement_score > 60:
        recommendations.append({
            "category": "visual_engagement",
            "suggestion": "Good foundation! Focus on increasing eye contact with the camera and varying your expressions to match your content's emotional tone.",
            "priority": "high",
            "score_impact": "Could improve score by 15-20 points",
            "coaching_depth": "foundational",
            "next_steps": ["Daily eye contact practice", "Expression mirroring exercises", "Energy calibration training"]
        })
    else:
        recommendations.append({
            "category": "visual_engagement",
            "suggestion": "Let's build your visual presence! Focus on being fully present on camera - imagine speaking to a close friend. Practice maintaining steady eye contact and authentic facial expressions.",
            "priority": "critical", 
            "score_impact": "Fundamental for audience connection",
            "coaching_depth": "foundational",
            "next_steps": ["Start with 5-min practice sessions", "Use teleprompter apps for eye contact", "Work with presentation coach"]
        })
    
    # EMOTIONAL CONSISTENCY RECOMMENDATIONS
    emotion_variability = insights['facial_analysis']['emotion_consistency']['variability_score']
    if emotion_variability > 0.8:
        recommendations.append({
            "category": "emotional_control",
            "suggestion": "Your emotions vary significantly throughout the presentation. This could indicate nervousness or lack of preparation. Practice with consistent energy levels.",
            "priority": "high",
            "score_impact": "Consistency builds trust with audience",
            "coaching_depth": "intermediate",
            "next_steps": ["Breathing exercises before presenting", "Rehearse with consistent energy", "Develop pre-presentation routine"]
        })
    
    # OPENING, MIDDLE, CLOSING ANALYSIS
    opening_confidence = emotional_patterns.get('opening_confidence', 0)
    closing_impact = emotional_patterns.get('closing_impact', 0)
    
    if opening_confidence < 0.6:
        recommendations.append({
            "category": "opening_presence",
            "suggestion": "Your opening lacks confidence. Start strong! Practice your first 30 seconds until it's second nature. A confident opening sets the tone for everything.",
            "priority": "high",
            "score_impact": "First impressions are crucial",
            "coaching_depth": "foundational",
            "next_steps": ["Memorize opening word-for-word", "Power pose before starting", "Practice opening 20+ times"]
        })
    
    if closing_impact < 0.7:
        recommendations.append({
            "category": "closing_impact", 
            "suggestion": "Your closing could be more impactful. End with conviction and energy. Your last impression should leave the audience inspired and clear on next steps.",
            "priority": "medium",
            "score_impact": "Strong endings create lasting impressions",
            "coaching_depth": "intermediate", 
            "next_steps": ["Craft memorable closing statement", "Practice ending with eye contact", "Develop signature closing gesture"]
        })
    
    # STRESS INDICATORS
    stress_indicators = emotional_patterns.get('stress_indicators', [])
    if stress_indicators:
        recommendations.append({
            "category": "stress_management",
            "suggestion": f"Detected stress indicators: {', '.join(stress_indicators)}. Consider stress management techniques before and during presentations.",
            "priority": "high",
            "score_impact": "Stress undermines message delivery",
            "coaching_depth": "foundational",
            "next_steps": ["Learn progressive muscle relaxation", "Practice mindfulness techniques", "Develop pre-presentation calm-down routine"]
        })
    
    # COACHING INSIGHTS BASED RECOMMENDATIONS
    coaching_insights = insights.get('coaching_insights', {})
    speaker_archetype = coaching_insights.get('speaker_archetype', '')
    
    if speaker_archetype == "analytical":
        recommendations.append({
            "category": "style_adaptation",
            "suggestion": "You have an analytical presentation style. Balance your data-driven approach with more emotional connection and storytelling elements.",
            "priority": "medium",
            "score_impact": "Emotional connection enhances analytical content",
            "coaching_depth": "advanced",
            "next_steps": ["Add personal anecdotes", "Use metaphors for complex concepts", "Practice emotional inflection"]
        })
    elif speaker_archetype == "enthusiastic":
        recommendations.append({
            "category": "style_refinement",
            "suggestion": "Your enthusiasm is a strength! Channel it strategically - use high energy for key points and dial back slightly for complex explanations.",
            "priority": "low",
            "score_impact": "Strategic energy use increases impact",
            "coaching_depth": "advanced",
            "next_steps": ["Map energy levels to content", "Practice dynamic range", "Record to calibrate enthusiasm"]
        })
    
    return recommendations

def generate_comprehensive_coaching_insights(insights: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive coaching insights for the presenter"""
    
    coaching_data = {
        "personality_style": "",
        "communication_strengths": [],
        "growth_opportunities": [],
        "speaker_archetype": "",
        "recommended_techniques": [],
        "development_stage": "",
        "personalized_practice_plan": []
    }
    
    # Analyze presenter's development stage
    engagement_score = insights['presentation_quality']['visual_engagement']
    emotion_consistency = insights['facial_analysis']['emotion_consistency']['variability_score']
    confidence_indicators = len(insights['visual_sentiment']['confidence_indicators'])
    
    if engagement_score > 85 and emotion_consistency < 0.3 and confidence_indicators > 3:
        coaching_data['development_stage'] = "advanced"
        coaching_data['personalized_practice_plan'] = [
            "Focus on master-level techniques like micro-expression control",
            "Practice storytelling integration with emotional arcs",
            "Develop signature presentation techniques",
            "Consider professional speaking coaching certification"
        ]
    elif engagement_score > 70 and emotion_consistency < 0.5:
        coaching_data['development_stage'] = "intermediate"
        coaching_data['personalized_practice_plan'] = [
            "Practice consistent energy maintenance throughout presentation",
            "Work on smooth emotional transitions",
            "Record weekly practice sessions for self-analysis",
            "Join presentation skills groups like Toastmasters"
        ]
    else:
        coaching_data['development_stage'] = "foundational"
        coaching_data['personalized_practice_plan'] = [
            "Start with 5-minute daily mirror practice",
            "Focus on basic eye contact and posture",
            "Use smartphone for recording practice sessions",
            "Work with presentation coach or mentor"
        ]
    
    # Analyze communication strengths
    if insights['presentation_quality']['body_language']['eye_contact_rating'] > 80:
        coaching_data['communication_strengths'].append("Exceptional eye contact builds strong audience connection")
    
    if insights['visual_sentiment']['overall_tone'] in ['positive', 'very_positive']:
        coaching_data['communication_strengths'].append("Positive emotional tone creates engaging atmosphere")
    
    emotional_arc = insights['visual_sentiment']['emotional_patterns']['emotional_arc']
    if emotional_arc == "consistently_strong":
        coaching_data['communication_strengths'].append("Maintains consistent professional energy throughout")
    
    # Identify growth opportunities
    smile_percentage = insights['facial_analysis']['facial_expressions']['smile_percentage']
    if smile_percentage < 30:
        coaching_data['growth_opportunities'].append("Increase natural smile frequency to enhance approachability")
    
    if emotion_consistency > 0.7:
        coaching_data['growth_opportunities'].append("Develop emotional consistency and control techniques")
    
    stress_indicators = insights['visual_sentiment']['emotional_patterns']['stress_indicators']
    if stress_indicators:
        coaching_data['growth_opportunities'].append("Implement stress management techniques for calmer delivery")
    
    return coaching_data

def analyze_emotional_patterns(insights: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze emotional patterns throughout the presentation for deeper insights"""
    
    emotion_timeline = insights['facial_analysis']['emotion_timeline']
    segments = insights['visual_sentiment']['segments']
    
    patterns = {
        "opening_confidence": 0,
        "mid_presentation_energy": 0,
        "closing_impact": 0,
        "stress_indicators": [],
        "engagement_peaks": [],
        "emotional_arc": "unknown"
    }
    
    if not emotion_timeline:
        return patterns
    
    # Analyze opening (first 20% of presentation)
    total_duration = len(emotion_timeline)
    opening_segment = emotion_timeline[:max(1, total_duration // 5)]
    
    if opening_segment:
        confidence_emotions = ['confidence', 'joy', 'neutral']
        opening_confidence_scores = []
        
        for moment in opening_segment:
            if moment.get('emotion') in confidence_emotions:
                opening_confidence_scores.append(moment.get('confidence', 0))
        
        patterns['opening_confidence'] = sum(opening_confidence_scores) / len(opening_confidence_scores) if opening_confidence_scores else 0
    
    # Analyze middle section (middle 60%)
    start_mid = total_duration // 5
    end_mid = total_duration * 4 // 5
    mid_segment = emotion_timeline[start_mid:end_mid]
    
    if mid_segment:
        energy_emotions = ['joy', 'confidence', 'surprise']
        energy_scores = []
        
        for moment in mid_segment:
            if moment.get('emotion') in energy_emotions:
                energy_scores.append(moment.get('confidence', 0))
        
        patterns['mid_presentation_energy'] = sum(energy_scores) / len(energy_scores) if energy_scores else 0
    
    # Analyze closing (last 20%)
    closing_segment = emotion_timeline[max(0, total_duration * 4 // 5):]
    
    if closing_segment:
        impact_emotions = ['confidence', 'joy']
        closing_scores = []
        
        for moment in closing_segment:
            if moment.get('emotion') in impact_emotions:
                closing_scores.append(moment.get('confidence', 0))
        
        patterns['closing_impact'] = sum(closing_scores) / len(closing_scores) if closing_scores else 0
    
    # Detect stress indicators
    stress_emotions = ['fear', 'sadness', 'anger']
    stress_moments = [moment for moment in emotion_timeline if moment.get('emotion') in stress_emotions and moment.get('confidence', 0) > 0.6]
    
    if len(stress_moments) > total_duration * 0.2:  # More than 20% stress moments
        patterns['stress_indicators'].append("High stress levels detected")
    
    if len(stress_moments) > 0:
        patterns['stress_indicators'].append(f"Stress detected at {len(stress_moments)} moments")
    
    # Find engagement peaks (high confidence + positive emotions)
    engagement_peaks = []
    for i, moment in enumerate(emotion_timeline):
        if moment.get('emotion') in ['joy', 'confidence'] and moment.get('confidence', 0) > 0.8:
            engagement_peaks.append({
                "timestamp": moment.get('timestamp', f"moment_{i}"),
                "emotion": moment.get('emotion"),
                "confidence": moment.get('confidence')
            })
    
    patterns['engagement_peaks'] = engagement_peaks[:5]  # Top 5 peaks
    
    # Determine emotional arc
    opening_score = patterns['opening_confidence']
    mid_score = patterns['mid_presentation_energy'] 
    closing_score = patterns['closing_impact']
    
    if opening_score > 0.7 and mid_score > 0.7 and closing_score > 0.7:
        patterns['emotional_arc'] = "consistently_strong"
    elif opening_score < 0.5 and closing_score > 0.7:
        patterns['emotional_arc'] = "building_confidence"
    elif opening_score > 0.7 and closing_score < 0.5:
        patterns['emotional_arc'] = "fading_energy"
    elif mid_score > max(opening_score, closing_score):
        patterns['emotional_arc'] = "peak_in_middle"
    else:
        patterns['emotional_arc'] = "inconsistent"
    
    return patterns

def determine_speaker_archetype(insights: Dict[str, Any]) -> str:
    """Determine the speaker's presentation archetype for personalized coaching"""
    
    engagement_score = insights['presentation_quality']['visual_engagement']
    emotion_timeline = insights['facial_analysis']['emotion_timeline']
    confidence_indicators = insights['visual_sentiment']['confidence_indicators']
    
    # Analyze dominant emotions
    emotion_counts = {}
    for moment in emotion_timeline:
        emotion = moment.get('emotion', 'neutral')
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    
    dominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else 'neutral'
    
    # Determine archetype based on patterns
    if dominant_emotion in ['joy', 'confidence'] and engagement_score > 80:
        return "enthusiastic_connector"
    elif dominant_emotion == 'neutral' and len(confidence_indicators) > 2:
        return "analytical_expert"
    elif engagement_score > 85 and 'High' in str(confidence_indicators):
        return "natural_leader"
    elif engagement_score < 60 and dominant_emotion in ['neutral', 'fear']:
        return "developing_speaker"
    elif dominant_emotion == 'confidence' and engagement_score > 70:
        return "confident_professional"
    else:
        return "balanced_communicator"
