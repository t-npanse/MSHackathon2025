import azure.functions as func
import datetime
import json
import logging
import utils

app = func.FunctionApp()

@app.route(route="analyze_transcript", auth_level=func.AuthLevel.ANONYMOUS)
def analyze_transcript(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    try:
        vtt_text = req.get_body().decode("utf-8")
    except Exception:
        return func.HttpResponse("Invalid request body", status_code=400)

    plain_text, duration = utils.strip_vtt(vtt_text)
    metrics = utils.transcript_metrics(plain_text, duration)
    pause_analysis = utils.analyze_pauses_from_vtt(vtt_text)
    
    # Combine results
    full_analysis = {
        **metrics,
        "pause_analysis": pause_analysis,
        "timestamp": datetime.datetime.now().isoformat()
    }

    return func.HttpResponse(
        json.dumps(full_analysis, indent=2),
        mimetype="application/json",
        status_code=200
    )

@app.function_name(name="sentiment_summary")
@app.route(route="sentiment_summary", auth_level=func.AuthLevel.ANONYMOUS)
def sentiment_summary(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("sentiment_summary triggered")

    try:
        text = req.get_body().decode("utf-8")
        if not text.strip():
            raise ValueError()
    except Exception:
        return func.HttpResponse("Request body must contain text.", status_code=400)

    scores = utils.sentiment_scores(text)

    return func.HttpResponse(
        json.dumps(scores, indent=2),
        mimetype="application/json",
        status_code=200
    )

@app.function_name(name="full_presentation_analysis")
@app.route(route="full_presentation_analysis", auth_level=func.AuthLevel.ANONYMOUS)
def full_presentation_analysis(req: func.HttpRequest) -> func.HttpResponse:
    """Enhanced comprehensive analysis of presentation transcript."""
    logging.info("full_presentation_analysis triggered")

    try:
        req_json = req.get_json()
        vtt_text = req_json.get('transcript', '')
        
        if not vtt_text.strip():
            raise ValueError("Transcript is required")
            
    except Exception as e:
        return func.HttpResponse(f"Invalid request: {str(e)}", status_code=400)

    # Extract plain text and duration
    plain_text, duration = utils.strip_vtt(vtt_text)
    
    # Perform enhanced analysis
    enhanced_metrics = utils.enhanced_transcript_metrics(plain_text, duration, vtt_text)
    pause_analysis = utils.analyze_pauses_from_vtt(vtt_text)
    sentiment = utils.sentiment_scores(plain_text)
    
    # Generate detailed recommendations
    recommendations = utils.generate_detailed_recommendations(enhanced_metrics)
    
    # Create executive summary
    executive_summary = utils.create_executive_summary(enhanced_metrics)
    
    # Compile comprehensive report
    comprehensive_report = {
        "report_metadata": {
            "analysis_timestamp": datetime.datetime.now().isoformat(),
            "transcript_length": len(plain_text),
            "analysis_version": "2.0_enhanced"
        },
        "executive_summary": executive_summary,
        "detailed_analysis": {
            "speech_metrics": enhanced_metrics,
            "pause_analysis": pause_analysis,
            "sentiment_analysis": sentiment
        },
        "recommendations": recommendations,
        "coaching_insights": generate_coaching_insights(enhanced_metrics, pause_analysis, sentiment)
    }

    return func.HttpResponse(
        json.dumps(comprehensive_report, indent=2),
        mimetype="application/json",
        status_code=200
    )

@app.function_name(name="analyze_combined")
@app.route(route="analyze_combined", auth_level=func.AuthLevel.ANONYMOUS)
def analyze_combined(req: func.HttpRequest) -> func.HttpResponse:
    """Simplified endpoint for chat interface compatibility."""
    logging.info("analyze_combined triggered")

    try:
        req_json = req.get_json()
        transcript_text = req_json.get('transcript', '')
        
        if not transcript_text.strip():
            raise ValueError("Transcript is required")
            
    except Exception as e:
        return func.HttpResponse(f"Invalid request: {str(e)}", status_code=400)

    # Handle both VTT and plain text
    if "WEBVTT" in transcript_text or "-->" in transcript_text:
        # VTT format
        plain_text, duration = utils.strip_vtt(transcript_text)
        pause_analysis = utils.analyze_pauses_from_vtt(transcript_text)
    else:
        # Plain text - estimate duration
        plain_text = transcript_text
        word_count = len(plain_text.split())
        duration = word_count / 150 * 60  # Assume 150 WPM average
        pause_analysis = {"pauses": [], "avg_pause": 0, "pause_rate": 0, "total_pause_time": 0}

    # Perform enhanced analysis
    enhanced_metrics = utils.enhanced_transcript_metrics(plain_text, duration, transcript_text)
    sentiment = utils.sentiment_scores(plain_text)
    recommendations = utils.generate_detailed_recommendations(enhanced_metrics)
    
    # Format for chat interface
    analysis_result = {
        "success": True,
        "analysis": {
            "speech_pace": {
                "words_per_minute": enhanced_metrics["basic_metrics"]["wpm"],
                "pace_category": enhanced_metrics["speech_patterns"]["pace_analysis"]["category"],
                "pause_percentage": round((pause_analysis.get("total_pause_time", 0) / duration) * 100, 1) if duration > 0 else 0
            },
            "filler_words": {
                "total_count": enhanced_metrics["filler_analysis"]["total_fillers"],
                "rate_per_minute": enhanced_metrics["filler_analysis"]["filler_rate_per_minute"],
                "breakdown": {
                    "hesitation": enhanced_metrics["filler_analysis"]["hesitation_fillers"]["count"],
                    "discourse_markers": enhanced_metrics["filler_analysis"]["discourse_markers"]["count"]
                }
            },
            "sentiment": {
                "label": sentiment["overall"],
                "score": sentiment["positive_pct"],
                "confidence": round((sentiment["positive_pct"] + (1 - sentiment["negative_pct"])) / 2, 2)
            },
            "presentation_quality": {
                "overall_score": enhanced_metrics["presentation_scores"]["overall_quality"]["overall_score"],
                "grade": enhanced_metrics["presentation_scores"]["overall_quality"]["grade"],
                "confidence_level": enhanced_metrics["presentation_scores"]["confidence_score"]["level"],
                "professional_readiness": enhanced_metrics["presentation_scores"]["professional_readiness"]["level"]
            },
            "recommendations": format_recommendations_for_chat(recommendations)
        },
        "timestamp": datetime.datetime.now().isoformat()
    }

    return func.HttpResponse(
        json.dumps(analysis_result, indent=2),
        mimetype="application/json",
        status_code=200
    )

def generate_coaching_insights(metrics: Dict, pauses: Dict, sentiment: Dict) -> Dict:
    """Generate professional coaching insights."""
    insights = {
        "presentation_style": analyze_presentation_style(metrics),
        "audience_impact": predict_audience_impact(metrics, sentiment),
        "improvement_priority": rank_improvement_areas(metrics),
        "benchmarking": compare_to_benchmarks(metrics)
    }
    return insights

def analyze_presentation_style(metrics: Dict) -> Dict:
    """Determine presenter's natural style and characteristics."""
    wpm = metrics["basic_metrics"]["wpm"]
    energy = metrics["speech_patterns"]["energy_levels"]["energy_level"]
    confidence = metrics["presentation_scores"]["confidence_score"]["level"]
    
    # Determine style
    if wpm > 160 and energy in ["high_energy", "moderate_energy"]:
        style = "dynamic_energetic"
        description = "Fast-paced, energetic presenter who engages through enthusiasm"
    elif wpm < 130 and confidence in ["very_confident", "confident"]:
        style = "thoughtful_deliberate"
        description = "Measured, thoughtful presenter who emphasizes depth over pace"
    elif confidence in ["moderately_confident", "needs_confidence_building"]:
        style = "developing_presenter"
        description = "Developing presentation skills, building confidence and fluency"
    else:
        style = "balanced_professional"
        description = "Well-balanced presentation style with good fundamentals"
    
    return {
        "style_category": style,
        "description": description,
        "natural_strengths": identify_natural_strengths(metrics),
        "style_recommendations": get_style_specific_tips(style)
    }

def predict_audience_impact(metrics: Dict, sentiment: Dict) -> Dict:
    """Predict how audience might respond to this presentation."""
    overall_score = metrics["presentation_scores"]["overall_quality"]["overall_score"]
    energy_level = metrics["speech_patterns"]["energy_levels"]["energy_level"]
    
    # Engagement prediction
    if overall_score >= 80 and energy_level in ["high_energy", "moderate_energy"]:
        engagement = "high"
        description = "Audience likely to be highly engaged and attentive"
    elif overall_score >= 65:
        engagement = "moderate"
        description = "Audience likely to remain interested with occasional attention drifts"
    else:
        engagement = "low"
        description = "Risk of losing audience attention, may struggle to maintain engagement"
    
    # Comprehension prediction
    wpm = metrics["basic_metrics"]["wpm"]
    if 130 <= wpm <= 160:
        comprehension = "high"
    elif wpm < 120 or wpm > 180:
        comprehension = "low"
    else:
        comprehension = "moderate"
    
    return {
        "predicted_engagement": engagement,
        "engagement_description": description,
        "comprehension_level": comprehension,
        "credibility_factors": assess_credibility_factors(metrics, sentiment)
    }

def rank_improvement_areas(metrics: Dict) -> List[Dict]:
    """Rank areas for improvement by impact and difficulty."""
    improvements = []
    
    # Check filler words
    filler_rate = metrics["filler_analysis"]["filler_rate_per_minute"]
    if filler_rate > 5:
        improvements.append({
            "area": "Filler Word Reduction",
            "current_score": max(0, 100 - filler_rate * 10),
            "potential_impact": "high",
            "difficulty": "medium",
            "time_to_improve": "2-4 weeks"
        })
    
    # Check speaking pace
    wpm = metrics["basic_metrics"]["wpm"]
    if wpm < 120 or wpm > 180:
        improvements.append({
            "area": "Speaking Pace Optimization",
            "current_score": max(0, 100 - abs(wpm - 145) * 2),
            "potential_impact": "high",
            "difficulty": "medium",
            "time_to_improve": "3-6 weeks"
        })
    
    # Check confidence language
    weak_count = metrics["language_confidence"]["weak_language_indicators"]["count"]
    if weak_count > 3:
        improvements.append({
            "area": "Confident Language Usage",
            "current_score": max(0, 100 - weak_count * 5),
            "potential_impact": "medium",
            "difficulty": "high",
            "time_to_improve": "1-3 months"
        })
    
    return sorted(improvements, key=lambda x: x["potential_impact"], reverse=True)

def compare_to_benchmarks(metrics: Dict) -> Dict:
    """Compare performance to industry benchmarks."""
    benchmarks = {
        "professional_presentations": {
            "optimal_wpm": "140-160",
            "max_filler_rate": "3 per minute",
            "confidence_threshold": "75+",
            "professional_vocab_density": "2%+"
        },
        "your_performance": {
            "wpm": metrics["basic_metrics"]["wpm"],
            "filler_rate": metrics["filler_analysis"]["filler_rate_per_minute"],
            "confidence_score": metrics["presentation_scores"]["confidence_score"]["score"],
            "professional_vocab_density": metrics["language_confidence"]["professional_vocabulary"]["density"]
        }
    }
    
    # Calculate percentile estimates
    wpm = metrics["basic_metrics"]["wpm"]
    if 140 <= wpm <= 160:
        pace_percentile = 85
    elif 120 <= wpm <= 180:
        pace_percentile = 65
    else:
        pace_percentile = 30
    
    filler_rate = metrics["filler_analysis"]["filler_rate_per_minute"]
    if filler_rate <= 3:
        fluency_percentile = 85
    elif filler_rate <= 6:
        fluency_percentile = 60
    else:
        fluency_percentile = 25
    
    return {
        "benchmarks": benchmarks,
        "estimated_percentiles": {
            "speaking_pace": pace_percentile,
            "fluency": fluency_percentile,
            "overall_presentation_skill": (pace_percentile + fluency_percentile) // 2
        }
    }

def identify_natural_strengths(metrics: Dict) -> List[str]:
    """Identify presenter's natural strengths."""
    strengths = []
    
    if metrics["basic_metrics"]["wpm"] >= 130 and metrics["basic_metrics"]["wpm"] <= 160:
        strengths.append("Natural speaking pace")
    
    if metrics["filler_analysis"]["filler_rate_per_minute"] <= 5:
        strengths.append("Good fluency and flow")
    
    if metrics["presentation_scores"]["confidence_score"]["score"] >= 70:
        strengths.append("Confident delivery")
    
    if metrics["language_confidence"]["professional_vocabulary"]["density"] >= 2:
        strengths.append("Strong professional vocabulary")
    
    return strengths

def get_style_specific_tips(style: str) -> List[str]:
    """Get personalized tips based on presentation style."""
    tips = {
        "dynamic_energetic": [
            "Use your natural energy as a strength, but ensure clarity isn't sacrificed for pace",
            "Practice strategic pauses to let key points sink in",
            "Channel enthusiasm into varied vocal inflection"
        ],
        "thoughtful_deliberate": [
            "Leverage your measured approach by emphasizing key transitions",
            "Use your natural pauses to build anticipation",
            "Consider adding more energy at crucial moments"
        ],
        "developing_presenter": [
            "Focus on building one skill at a time - start with pace or filler reduction",
            "Practice with familiar topics to build confidence",
            "Record yourself regularly to track improvement"
        ],
        "balanced_professional": [
            "Fine-tune advanced techniques like storytelling and audience interaction",
            "Work on varying energy levels throughout the presentation",
            "Focus on executive presence and gravitas"
        ]
    }
    return tips.get(style, ["Continue developing your unique presentation style"])

def assess_credibility_factors(metrics: Dict, sentiment: Dict) -> Dict:
    """Assess factors that impact speaker credibility."""
    credibility_score = 50  # Base score
    
    # Professional vocabulary increases credibility
    prof_vocab = metrics["language_confidence"]["professional_vocabulary"]["density"]
    credibility_score += min(prof_vocab * 5, 25)
    
    # Weak language decreases credibility
    weak_lang = metrics["language_confidence"]["weak_language_indicators"]["density"]
    credibility_score -= weak_lang * 3
    
    # Excessive fillers decrease credibility
    filler_rate = metrics["filler_analysis"]["filler_rate_per_minute"]
    if filler_rate > 8:
        credibility_score -= 20
    elif filler_rate > 5:
        credibility_score -= 10
    
    # Positive sentiment increases credibility
    if sentiment["overall"] == "positive":
        credibility_score += 10
    
    credibility_score = max(0, min(100, credibility_score))
    
    return {
        "credibility_score": round(credibility_score, 1),
        "factors": {
            "professional_vocabulary": prof_vocab,
            "uncertain_language": weak_lang,
            "fluency": filler_rate,
            "overall_tone": sentiment["overall"]
        }
    }

def format_recommendations_for_chat(recommendations: Dict) -> List[str]:
    """Format recommendations for simple display in chat interface."""
    formatted = []
    
    # Add immediate actions
    for action in recommendations["immediate_actions"][:3]:  # Top 3
        formatted.append(f"{action['category']}: {action['specific_tip']}")
    
    # Add practice exercises
    for exercise in recommendations["practice_exercises"][:2]:  # Top 2
        formatted.append(f"Practice: {exercise}")
    
    return formatted

