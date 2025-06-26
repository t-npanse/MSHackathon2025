import re
from typing import Dict, Tuple, List
import statistics
import math

FILLERS = re.compile(r'\b(um+|uh+|like|you know|so|actually|basically|literally)\b', re.I)

# Enhanced filler categorization
HESITATION_FILLERS = re.compile(r'\b(um+|uh+|er+|ah+)\b', re.I)
DISCOURSE_MARKERS = re.compile(r'\b(like|you know|so|actually|basically|literally|right|okay)\b', re.I)
INTENSIFIERS = re.compile(r'\b(very|really|totally|absolutely|completely|extremely)\b', re.I)

# Professional vocabulary indicators
PROFESSIONAL_TERMS = re.compile(r'\b(implement|analyze|optimize|strategy|solution|framework|methodology|approach|evaluate|assess|demonstrate|indicate|suggest|recommend|conclude)\b', re.I)
WEAK_LANGUAGE = re.compile(r'\b(maybe|perhaps|kind of|sort of|i think|i guess|probably|might|could be)\b', re.I)

def strip_vtt(vtt_text: str) -> Tuple[str, float]:
    """Return plain transcript text and total duration (in seconds)."""
    lines = []
    start_time = end_time = 0.0

    for line in vtt_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "-->" in line:          # a timestamp line
            start, end = line.split("-->")
            # convert 00:00:04.820 to seconds
            h1,m1,s1 = parse_ts(start)
            h2,m2,s2 = parse_ts(end)
            if start_time == 0.0:
                start_time = h1*3600 + m1*60 + s1
            end_time = h2*3600 + m2*60 + s2
        elif not line.isdigit():   # skip cue numbers
            lines.append(line)

    duration = max(0.1, end_time - start_time)
    return "\n".join(lines), duration

def parse_ts(ts: str) -> Tuple[int,int,float]:
    h, m, rest = ts.strip().split(":")
    return int(h), int(m), float(rest.replace(",", "."))

def analyze_pauses_from_vtt(vtt_text: str) -> Dict:
    """Analyze pauses between speech segments from VTT timestamps."""
    timestamps = []
    
    for line in vtt_text.splitlines():
        line = line.strip()
        if "-->" in line:
            start, end = line.split("-->")
            h1,m1,s1 = parse_ts(start)
            h2,m2,s2 = parse_ts(end)
            start_time = h1*3600 + m1*60 + s1
            end_time = h2*3600 + m2*60 + s2
            timestamps.append((start_time, end_time))
    
    if len(timestamps) < 2:
        return {"pauses": [], "avg_pause": 0, "long_pauses": 0, "pause_rate": 0}
    
    # Calculate gaps between speech segments
    pauses = []
    for i in range(1, len(timestamps)):
        gap = timestamps[i][0] - timestamps[i-1][1]
        if gap > 0.5:  # Only count pauses longer than 0.5 seconds
            pauses.append(gap)
    
    if not pauses:
        return {"pauses": [], "avg_pause": 0, "long_pauses": 0, "pause_rate": 0}
    
    avg_pause = statistics.mean(pauses)
    long_pauses = len([p for p in pauses if p > 3.0])  # Pauses longer than 3 seconds
    pause_rate = len(pauses) / (len(timestamps) / 60)  # Pauses per minute
    
    return {
        "pauses": pauses,
        "avg_pause": round(avg_pause, 2),
        "long_pauses": long_pauses,
        "pause_rate": round(pause_rate, 1),
        "total_pause_time": round(sum(pauses), 2)
    }

def transcript_metrics(text: str, duration_sec: float) -> Dict:
    words = text.split()
    word_count = len(words)
    wpm = round((word_count / duration_sec) * 60, 1)
    filler_matches = FILLERS.findall(text)
    filler_count = len(filler_matches)
    
    # Calculate filler rate (fillers per minute)
    filler_rate = round((filler_count / duration_sec) * 60, 1)
    
    # Analyze sentence structure
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    avg_sentence_length = round(word_count / max(1, len(sentences)), 1)
    
    return {
        "word_count": word_count,
        "duration_sec": round(duration_sec, 1),
        "wpm": wpm,
        "filler_count": filler_count,
        "filler_rate": filler_rate,
        "filler_words": filler_matches,
        "sentence_count": len(sentences),
        "avg_sentence_length": avg_sentence_length,
        "speech_quality": assess_speech_quality(wpm, filler_rate)
    }

def assess_speech_quality(wpm: float, filler_rate: float) -> str:
    """Assess overall speech quality based on pace and filler usage."""
    if wpm < 120:
        pace = "slow"
    elif wpm > 180:
        pace = "fast"
    else:
        pace = "good"
    
    if filler_rate > 10:
        fillers = "high"
    elif filler_rate > 5:
        fillers = "moderate"
    else:
        fillers = "low"
    
    if pace == "good" and fillers == "low":
        return "excellent"
    elif pace == "good" or fillers == "low":
        return "good"
    else:
        return "needs_improvement"


from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import os

def get_text_analytics_client() -> TextAnalyticsClient:
    endpoint = os.environ["COG_ENDPOINT"]
    key      = os.environ["COG_KEY"]
    return TextAnalyticsClient(endpoint, AzureKeyCredential(key))

def sentiment_scores(text: str) -> dict:
    """Return overall label and positive/negative percentages."""
    client = get_text_analytics_client()
    result = client.analyze_sentiment([text])[0]  # single doc
    overall = result.sentiment          # 'positive' | 'neutral' | 'negative' | 'mixed'
    pos = result.confidence_scores.positive
    neg = result.confidence_scores.negative
    return {
        "overall": overall,
        "positive_pct": round(pos, 2),
        "negative_pct": round(neg, 2)
    }

def enhanced_transcript_metrics(text: str, duration_sec: float, vtt_text: str = "") -> Dict:
    """Comprehensive speech analysis with detailed insights."""
    words = text.split()
    word_count = len(words)
    wpm = round((word_count / duration_sec) * 60, 1)
    
    # Basic filler analysis
    filler_matches = FILLERS.findall(text)
    filler_count = len(filler_matches)
    filler_rate = round((filler_count / duration_sec) * 60, 1)
    
    # Enhanced filler categorization
    hesitation_fillers = HESITATION_FILLERS.findall(text)
    discourse_markers = DISCOURSE_MARKERS.findall(text)
    
    # Language confidence analysis
    professional_terms = PROFESSIONAL_TERMS.findall(text)
    weak_language = WEAK_LANGUAGE.findall(text)
    intensifiers = INTENSIFIERS.findall(text)
    
    # Sentence structure analysis
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    sentence_lengths = [len(s.split()) for s in sentences]
    avg_sentence_length = round(statistics.mean(sentence_lengths) if sentence_lengths else 0, 1)
    sentence_variety = calculate_sentence_variety(sentence_lengths)
    
    # Speaking pattern analysis
    pace_analysis = analyze_speaking_pace(text, duration_sec)
    energy_analysis = analyze_energy_levels(text)
    clarity_metrics = analyze_clarity(text, words)
    
    # Professional presentation scoring
    confidence_score = calculate_confidence_score(
        weak_language, professional_terms, filler_rate, wpm
    )
    
    return {
        "basic_metrics": {
            "word_count": word_count,
            "duration_sec": round(duration_sec, 1),
            "wpm": wpm,
            "sentence_count": len(sentences),
            "avg_sentence_length": avg_sentence_length
        },
        "filler_analysis": {
            "total_fillers": filler_count,
            "filler_rate_per_minute": filler_rate,
            "hesitation_fillers": {
                "count": len(hesitation_fillers),
                "words": list(set(hesitation_fillers)),
                "rate": round((len(hesitation_fillers) / duration_sec) * 60, 1)
            },
            "discourse_markers": {
                "count": len(discourse_markers),
                "words": list(set(discourse_markers)),
                "rate": round((len(discourse_markers) / duration_sec) * 60, 1)
            }
        },
        "language_confidence": {
            "professional_vocabulary": {
                "count": len(professional_terms),
                "density": round((len(professional_terms) / word_count) * 100, 1),
                "examples": list(set(professional_terms))[:5]
            },
            "weak_language_indicators": {
                "count": len(weak_language),
                "density": round((len(weak_language) / word_count) * 100, 1),
                "examples": list(set(weak_language))[:5]
            },
            "intensifier_usage": {
                "count": len(intensifiers),
                "density": round((len(intensifiers) / word_count) * 100, 1)
            }
        },
        "speech_patterns": {
            "pace_analysis": pace_analysis,
            "energy_levels": energy_analysis,
            "clarity_metrics": clarity_metrics,
            "sentence_variety": sentence_variety
        },
        "presentation_scores": {
            "confidence_score": confidence_score,
            "overall_quality": assess_overall_quality(confidence_score, wpm, filler_rate),
            "professional_readiness": assess_professional_readiness(
                professional_terms, weak_language, filler_rate
            )
        }
    }

def calculate_sentence_variety(sentence_lengths: List[int]) -> Dict:
    """Analyze variety in sentence structure."""
    if not sentence_lengths:
        return {"variety_score": 0, "analysis": "No sentences detected"}
    
    std_dev = statistics.stdev(sentence_lengths) if len(sentence_lengths) > 1 else 0
    mean_length = statistics.mean(sentence_lengths)
    
    # Variety score based on standard deviation relative to mean
    variety_score = round(min(10, (std_dev / max(mean_length, 1)) * 10), 1)
    
    short_sentences = len([l for l in sentence_lengths if l < 8])
    medium_sentences = len([l for l in sentence_lengths if 8 <= l <= 15])
    long_sentences = len([l for l in sentence_lengths if l > 15])
    
    return {
        "variety_score": variety_score,
        "sentence_distribution": {
            "short_sentences": short_sentences,
            "medium_sentences": medium_sentences,
            "long_sentences": long_sentences
        },
        "analysis": interpret_sentence_variety(variety_score, short_sentences, medium_sentences, long_sentences)
    }

def analyze_speaking_pace(text: str, duration_sec: float) -> Dict:
    """Detailed pace analysis with recommendations."""
    words = text.split()
    word_count = len(words)
    wpm = (word_count / duration_sec) * 60
    
    # Categorize pace
    if wpm < 100:
        pace_category = "very_slow"
        pace_description = "Significantly slower than average"
    elif wpm < 120:
        pace_category = "slow"
        pace_description = "Slower than recommended"
    elif wpm <= 160:
        pace_category = "optimal"
        pace_description = "Within optimal range"
    elif wpm <= 180:
        pace_category = "fast"
        pace_description = "Faster than average"
    else:
        pace_category = "very_fast"
        pace_description = "Significantly faster than recommended"
    
    return {
        "wpm": round(wpm, 1),
        "category": pace_category,
        "description": pace_description,
        "optimal_range": "130-160 WPM for presentations",
        "recommendation": get_pace_recommendation(pace_category)
    }

def analyze_energy_levels(text: str) -> Dict:
    """Analyze energy and enthusiasm indicators."""
    # Count exclamation marks and emotional words
    exclamations = text.count('!')
    
    # Energy words
    high_energy_words = re.findall(r'\b(excited|amazing|fantastic|incredible|outstanding|excellent|wonderful|great|awesome|brilliant)\b', text, re.I)
    
    # Engagement words
    engagement_words = re.findall(r'\b(imagine|consider|think about|picture|visualize|let me show you|check this out)\b', text, re.I)
    
    # Question marks (audience engagement)
    questions = text.count('?')
    
    total_words = len(text.split())
    energy_density = (len(high_energy_words) + exclamations) / max(total_words, 1) * 100
    
    return {
        "energy_indicators": {
            "exclamations": exclamations,
            "high_energy_words": len(high_energy_words),
            "engagement_phrases": len(engagement_words),
            "questions": questions
        },
        "energy_density": round(energy_density, 2),
        "energy_level": categorize_energy_level(energy_density),
        "examples": {
            "energy_words": list(set(high_energy_words))[:3],
            "engagement_phrases": list(set(engagement_words))[:3]
        }
    }

def analyze_clarity(text: str, words: List[str]) -> Dict:
    """Analyze speech clarity indicators."""
    # Syllable complexity (approximation)
    complex_words = [w for w in words if len(w) > 7]
    
    # Repeated words (may indicate struggle for clarity)
    word_freq = {}
    for word in words:
        if len(word) > 3:  # Skip short words
            word_lower = word.lower()
            word_freq[word_lower] = word_freq.get(word_lower, 0) + 1
    
    repeated_words = {k: v for k, v in word_freq.items() if v > 3}
    
    # Average word length
    avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
    
    return {
        "vocabulary_complexity": {
            "complex_words": len(complex_words),
            "complexity_ratio": round(len(complex_words) / len(words) * 100, 1),
            "avg_word_length": round(avg_word_length, 1)
        },
        "repetition_analysis": {
            "repeated_words_count": len(repeated_words),
            "most_repeated": dict(sorted(repeated_words.items(), key=lambda x: x[1], reverse=True)[:3])
        }
    }

def calculate_confidence_score(weak_language: List, professional_terms: List, filler_rate: float, wpm: float) -> Dict:
    """Calculate overall confidence score."""
    # Start with base score
    confidence = 100
    
    # Deduct for weak language
    confidence -= len(weak_language) * 2
    
    # Add for professional vocabulary
    confidence += min(len(professional_terms) * 1.5, 15)
    
    # Deduct for excessive fillers
    if filler_rate > 10:
        confidence -= 20
    elif filler_rate > 5:
        confidence -= 10
    
    # Adjust for pace
    if wpm < 120 or wpm > 180:
        confidence -= 10
    
    confidence = max(0, min(100, confidence))
    
    return {
        "score": round(confidence, 1),
        "level": categorize_confidence(confidence),
        "factors": {
            "weak_language_count": len(weak_language),
            "professional_vocab_count": len(professional_terms),
            "filler_rate": filler_rate,
            "pace_appropriate": 120 <= wpm <= 180
        }
    }

def assess_overall_quality(confidence_score: float, wpm: float, filler_rate: float) -> Dict:
    """Comprehensive quality assessment."""
    # Weighted scoring
    pace_score = 100 if 130 <= wpm <= 160 else max(0, 100 - abs(wpm - 145) * 2)
    filler_score = max(0, 100 - filler_rate * 10)
    
    overall_score = (confidence_score * 0.4 + pace_score * 0.3 + filler_score * 0.3)
    
    if overall_score >= 85:
        grade = "A"
        description = "Excellent presentation delivery"
    elif overall_score >= 75:
        grade = "B"
        description = "Good presentation with minor improvements needed"
    elif overall_score >= 65:
        grade = "C"
        description = "Average presentation, several areas for improvement"
    elif overall_score >= 50:
        grade = "D"
        description = "Below average, significant improvement needed"
    else:
        grade = "F"
        description = "Poor delivery, major improvements required"
    
    return {
        "overall_score": round(overall_score, 1),
        "grade": grade,
        "description": description,
        "component_scores": {
            "confidence": round(confidence_score, 1),
            "pace": round(pace_score, 1),
            "fluency": round(filler_score, 1)
        }
    }

def assess_professional_readiness(professional_terms: List, weak_language: List, filler_rate: float) -> Dict:
    """Assess readiness for professional presentations."""
    readiness_score = 50  # Base score
    
    # Professional vocabulary bonus
    readiness_score += min(len(professional_terms) * 3, 30)
    
    # Penalty for weak language
    readiness_score -= len(weak_language) * 5
    
    # Penalty for excessive fillers
    if filler_rate > 8:
        readiness_score -= 20
    elif filler_rate > 5:
        readiness_score -= 10
    
    readiness_score = max(0, min(100, readiness_score))
    
    if readiness_score >= 80:
        level = "executive_ready"
        description = "Ready for high-stakes professional presentations"
    elif readiness_score >= 65:
        level = "professional_ready"
        description = "Suitable for most professional contexts"
    elif readiness_score >= 50:
        level = "developing"
        description = "Developing professional presentation skills"
    else:
        level = "needs_development"
        description = "Requires significant development for professional contexts"
    
    return {
        "readiness_score": round(readiness_score, 1),
        "level": level,
        "description": description
    }

# Helper functions for categorization
def interpret_sentence_variety(score: float, short: int, medium: int, long: int) -> str:
    if score >= 7:
        return "Excellent variety in sentence structure"
    elif score >= 5:
        return "Good mix of sentence lengths"
    elif score >= 3:
        return "Some variety, could be more dynamic"
    else:
        return "Limited sentence variety, tends to be monotonous"

def get_pace_recommendation(category: str) -> str:
    recommendations = {
        "very_slow": "Practice speaking more quickly. Record yourself and gradually increase pace.",
        "slow": "Increase speaking pace slightly for better engagement.",
        "optimal": "Excellent pace! Maintain this speed for clarity and engagement.",
        "fast": "Slow down slightly to ensure audience comprehension.",
        "very_fast": "Significantly reduce speaking pace. Practice pausing between ideas."
    }
    return recommendations.get(category, "Maintain current pace")

def categorize_energy_level(density: float) -> str:
    if density >= 3:
        return "high_energy"
    elif density >= 1.5:
        return "moderate_energy"
    elif density >= 0.5:
        return "low_moderate_energy"
    else:
        return "low_energy"

def categorize_confidence(score: float) -> str:
    if score >= 85:
        return "very_confident"
    elif score >= 70:
        return "confident"
    elif score >= 55:
        return "moderately_confident"
    else:
        return "needs_confidence_building"

def generate_detailed_recommendations(analysis_results: Dict) -> Dict:
    """Generate comprehensive, actionable recommendations."""
    recommendations = {
        "immediate_actions": [],
        "practice_exercises": [],
        "long_term_goals": [],
        "professional_development": []
    }
    
    # Extract key metrics
    wpm = analysis_results["basic_metrics"]["wpm"]
    filler_rate = analysis_results["filler_analysis"]["filler_rate_per_minute"]
    confidence_score = analysis_results["presentation_scores"]["confidence_score"]["score"]
    weak_language_count = analysis_results["language_confidence"]["weak_language_indicators"]["count"]
    
    # Pace recommendations
    if wpm < 120:
        recommendations["immediate_actions"].append({
            "category": "Speaking Pace",
            "action": "Increase your speaking speed",
            "specific_tip": f"Your current pace is {wpm} WPM. Aim for 130-160 WPM by practicing with a metronome or reading exercises.",
            "priority": "high"
        })
        recommendations["practice_exercises"].append("Practice reading news articles aloud, gradually increasing pace while maintaining clarity.")
    
    elif wpm > 180:
        recommendations["immediate_actions"].append({
            "category": "Speaking Pace",
            "action": "Slow down your delivery",
            "specific_tip": f"Your pace of {wpm} WPM is too fast. Practice deliberate pauses between sentences.",
            "priority": "high"
        })
        recommendations["practice_exercises"].append("Record yourself speaking and practice adding 2-second pauses between major points.")
    
    # Filler word recommendations
    if filler_rate > 8:
        recommendations["immediate_actions"].append({
            "category": "Fluency",
            "action": "Reduce filler word usage",
            "specific_tip": f"You use {filler_rate} filler words per minute. Replace 'um' and 'uh' with intentional pauses.",
            "priority": "high"
        })
        recommendations["practice_exercises"].append("Practice the '3-second rule': pause for 3 seconds instead of using filler words.")
    
    # Confidence recommendations
    if confidence_score < 70:
        recommendations["immediate_actions"].append({
            "category": "Confidence",
            "action": "Strengthen your language confidence",
            "specific_tip": "Replace uncertain phrases with definitive statements.",
            "priority": "medium"
        })
        
        if weak_language_count > 5:
            recommendations["practice_exercises"].append("Create a list of strong alternatives to weak phrases (e.g., 'I believe' instead of 'I think maybe').")
    
    # Professional vocabulary
    prof_vocab_count = analysis_results["language_confidence"]["professional_vocabulary"]["count"]
    if prof_vocab_count < 5:
        recommendations["professional_development"].append({
            "category": "Vocabulary",
            "goal": "Expand professional vocabulary",
            "strategy": "Incorporate industry-specific terms and action-oriented language into your presentations.",
            "timeline": "2-4 weeks"
        })
    
    # Sentence variety
    variety_score = analysis_results["speech_patterns"]["sentence_variety"]["variety_score"]
    if variety_score < 5:
        recommendations["practice_exercises"].append("Practice varying sentence length: short punchy statements followed by detailed explanations.")
    
    # Energy level recommendations
    energy_level = analysis_results["speech_patterns"]["energy_levels"]["energy_level"]
    if energy_level == "low_energy":
        recommendations["immediate_actions"].append({
            "category": "Engagement",
            "action": "Increase vocal energy and enthusiasm",
            "specific_tip": "Use more dynamic language, questions, and exclamation points in your delivery.",
            "priority": "medium"
        })
    
    # Long-term development goals
    overall_score = analysis_results["presentation_scores"]["overall_quality"]["overall_score"]
    if overall_score < 75:
        recommendations["long_term_goals"].append({
            "goal": "Achieve consistent presentation excellence",
            "milestones": [
                "Reduce filler words to less than 3 per minute",
                "Maintain 140-160 WPM speaking pace",
                "Increase professional vocabulary usage",
                "Develop confident, assertive language patterns"
            ],
            "timeline": "3-6 months"
        })
    
    return recommendations

def create_executive_summary(analysis_results: Dict) -> Dict:
    """Create a concise executive summary of the presentation analysis."""
    overall_quality = analysis_results["presentation_scores"]["overall_quality"]
    confidence = analysis_results["presentation_scores"]["confidence_score"]
    
    # Identify top strengths
    strengths = []
    areas_for_improvement = []
    
    # Pace analysis
    wpm = analysis_results["basic_metrics"]["wpm"]
    if 130 <= wpm <= 160:
        strengths.append("Optimal speaking pace for audience comprehension")
    elif wpm < 130:
        areas_for_improvement.append("Speaking pace too slow - may lose audience attention")
    else:
        areas_for_improvement.append("Speaking pace too fast - may reduce comprehension")
    
    # Filler analysis
    filler_rate = analysis_results["filler_analysis"]["filler_rate_per_minute"]
    if filler_rate < 3:
        strengths.append("Excellent fluency with minimal filler words")
    elif filler_rate < 6:
        strengths.append("Good fluency with acceptable filler word usage")
    else:
        areas_for_improvement.append(f"High filler word usage ({filler_rate}/min) reduces professionalism")
    
    # Confidence analysis
    if confidence["score"] >= 80:
        strengths.append("Strong, confident language throughout presentation")
    elif confidence["score"] >= 65:
        strengths.append("Generally confident delivery with room for improvement")
    else:
        areas_for_improvement.append("Language patterns suggest uncertainty - strengthen assertiveness")
    
    # Professional readiness
    prof_readiness = analysis_results["presentation_scores"]["professional_readiness"]
    
    return {
        "overall_assessment": {
            "grade": overall_quality["grade"],
            "score": overall_quality["overall_score"],
            "description": overall_quality["description"]
        },
        "key_strengths": strengths[:3],  # Top 3 strengths
        "priority_improvements": areas_for_improvement[:3],  # Top 3 areas
        "professional_readiness": {
            "level": prof_readiness["level"],
            "description": prof_readiness["description"]
        },
        "next_steps": generate_next_steps(overall_quality["overall_score"], confidence["score"])
    }

def generate_next_steps(overall_score: float, confidence_score: float) -> List[str]:
    """Generate specific next steps based on scores."""
    steps = []
    
    if overall_score < 60:
        steps.append("Focus on basic fluency: reduce filler words and establish consistent pace")
        steps.append("Practice with recorded sessions to identify specific improvement areas")
    elif overall_score < 75:
        steps.append("Refine delivery: work on sentence variety and professional vocabulary")
        steps.append("Join a speaking group (like Toastmasters) for regular practice")
    else:
        steps.append("Fine-tune advanced techniques: work on energy variation and audience engagement")
        steps.append("Seek opportunities for high-stakes presentations to build experience")
    
    if confidence_score < 70:
        steps.append("Develop assertive language patterns through deliberate practice")
    
    return steps
