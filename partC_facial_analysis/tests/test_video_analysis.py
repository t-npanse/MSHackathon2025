import pytest
import json
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils

class TestVideoAnalysis:
    
    @patch.dict(os.environ, {
        'CONTENT_UNDERSTANDING_ENDPOINT': 'https://test.cognitiveservices.azure.com',
        'CONTENT_UNDERSTANDING_KEY': 'test-key-123'
    })
    def test_get_content_understanding_client(self):
        """Test client configuration"""
        client = utils.get_content_understanding_client()
        
        assert client['endpoint'] == 'https://test.cognitiveservices.azure.com'
        assert client['key'] == 'test-key-123'
        assert 'Ocp-Apim-Subscription-Key' in client['headers']
    
    def test_extract_score_from_text(self):
        """Test score extraction from descriptive text"""
        assert utils.extract_score_from_text("excellent presentation") == 90
        assert utils.extract_score_from_text("good engagement") == 75
        assert utils.extract_score_from_text("average performance") == 60
        assert utils.extract_score_from_text("poor delivery") == 40
        assert utils.extract_score_from_text("unclear assessment") == 50
    
    def test_generate_presentation_insights(self):
        """Test insights generation from Content Understanding results"""
        # Mock Content Understanding response
        mock_result = {
            "documents": [
                {
                    "fields": {
                        "emotionDescription": {
                            "valueString": "The presenter appears confident and engaged",
                            "confidence": 0.85
                        },
                        "confidenceLevel": {
                            "valueString": "High",
                            "confidence": 0.90
                        },
                        "engagementScore": {
                            "valueString": "Strong visual engagement with good eye contact",
                            "confidence": 0.80
                        },
                        "presentationQuality": {
                            "valueString": "Professional delivery with clear communication",
                            "confidence": 0.88
                        }
                    }
                }
            ],
            "contentExtraction": {
                "faceGroupings": {
                    "groups": [
                        {
                            "id": "group1",
                            "instances": [{"timestamp": "00:01:00"}, {"timestamp": "00:02:00"}],
                            "representativeFace": {"confidence": 0.95}
                        }
                    ]
                },
                "transcript": "Hello everyone, welcome to my presentation...",
                "keyFrames": [
                    {
                        "timestamp": "00:00:30",
                        "description": "Presenter introducing the topic",
                        "confidence": 0.90
                    }
                ]
            }
        }
        
        insights = utils.generate_presentation_insights(mock_result)
        
        # Check structure
        assert "facial_analysis" in insights
        assert "visual_sentiment" in insights
        assert "presentation_quality" in insights
        assert "content_analysis" in insights
        assert "recommendations" in insights
        
        # Check specific values
        assert insights["facial_analysis"]["faces_detected"] == 1
        assert insights["visual_sentiment"]["confidence_indicators"] == ["High"]
        assert insights["content_analysis"]["transcript"] == "Hello everyone, welcome to my presentation..."
        assert len(insights["content_analysis"]["key_moments"]) == 1
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        # Mock insights with low engagement
        low_engagement_insights = {
            "presentation_quality": {"visual_engagement": 40},
            "visual_sentiment": {"confidence_indicators": ["Low"], "overall_tone": "needs_improvement"},
            "facial_analysis": {"faces_detected": 0}
        }
        
        recommendations = utils.generate_recommendations(low_engagement_insights)
        
        # Should have multiple high-priority recommendations
        assert len(recommendations) >= 3
        assert any(rec["priority"] == "critical" for rec in recommendations)
        assert any(rec["category"] == "visibility" for rec in recommendations)
        assert any(rec["category"] == "confidence" for rec in recommendations)
        
        # Mock insights with good engagement
        good_engagement_insights = {
            "presentation_quality": {"visual_engagement": 85},
            "visual_sentiment": {"confidence_indicators": ["High"], "overall_tone": "positive"},
            "facial_analysis": {"faces_detected": 1}
        }
        
        recommendations = utils.generate_recommendations(good_engagement_insights)
        
        # Should have fewer, lower-priority recommendations
        assert all(rec["priority"] in ["low", "medium"] for rec in recommendations)

if __name__ == "__main__":
    pytest.main([__file__])
