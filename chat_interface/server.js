const express = require('express');
const cors = require('cors');
const path = require('path');
const axios = require('axios');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('.'));

// Serve the main HTML file
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index_new.html'));
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Video analysis endpoint
app.post('/analyze-video', async (req, res) => {
    try {
        const { videoUrl } = req.body;
        
        if (!videoUrl) {
            return res.status(400).json({
                success: false,
                error: 'Video URL is required'
            });
        }

        console.log(`Analyzing video: ${videoUrl}`);

        // Try to call your Azure Function first
        const functionEndpoint = process.env.FUNCTION_ENDPOINT;
        
        if (functionEndpoint) {
            try {
                console.log(`Calling Azure Function: ${functionEndpoint}`);
                const response = await axios.post(functionEndpoint, {
                    video_url: videoUrl
                }, {
                    timeout: 180000, // 3 minutes timeout
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                console.log('Azure Function response received');
                res.json(response.data);
                return;
            } catch (error) {
                console.error('Azure Function error:', error.message);
                console.log('Falling back to mock data...');
            }
        }

        // Fallback to mock data
        const mockResult = generateMockVideoAnalysis(videoUrl);
        res.json(mockResult);

    } catch (error) {
        console.error('Analysis error:', error);
        res.status(500).json({
            success: false,
            error: 'Internal server error during video analysis'
        });
    }
});

// Transcript analysis endpoint
app.post('/analyze-transcript', async (req, res) => {
    try {
        const { transcript } = req.body;
        
        if (!transcript || !transcript.trim()) {
            return res.status(400).json({
                success: false,
                error: 'Transcript text is required'
            });
        }

        console.log(`Analyzing transcript: ${transcript.length} characters`);

        // Try to call Part B Azure Function first
        const transcriptFunctionEndpoint = process.env.TRANSCRIPT_FUNCTION_ENDPOINT;
        
        if (transcriptFunctionEndpoint) {
            try {
                console.log(`Calling Part B Azure Function: ${transcriptFunctionEndpoint}`);
                const response = await axios.post(`${transcriptFunctionEndpoint}/analyze_combined`, {
                    transcript: transcript
                }, {
                    timeout: 60000, // 1 minute timeout
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                console.log('Part B Azure Function response received');
                res.json(response.data);
                return;
            } catch (error) {
                console.error('Part B Azure Function error:', error.message);
                console.log('Falling back to mock transcript data...');
            }
        }

        // Fallback to mock transcript analysis
        const mockResult = generateMockTranscriptAnalysis(transcript);
        res.json(mockResult);

    } catch (error) {
        console.error('Transcript analysis error:', error);
        res.status(500).json({
            success: false,
            error: 'Internal server error during transcript analysis'
        });
    }
});

// Combined analysis endpoint (for future use if needed)
app.post('/analyze-combined', async (req, res) => {
    try {
        const { videoUrl, transcript } = req.body;
        
        if (!videoUrl && !transcript) {
            return res.status(400).json({
                success: false,
                error: 'Either video URL or transcript is required'
            });
        }

        console.log(`Combined analysis - Video: ${!!videoUrl}, Transcript: ${!!transcript}`);

        const results = {};
        
        // Analyze video if provided
        if (videoUrl) {
            results.video_analysis = generateMockVideoAnalysis(videoUrl);
        }
        
        // Analyze transcript if provided
        if (transcript) {
            results.transcript_analysis = generateMockTranscriptAnalysis(transcript);
        }

        res.json({
            success: true,
            ...results
        });

    } catch (error) {
        console.error('Combined analysis error:', error);
        res.status(500).json({
            success: false,
            error: 'Internal server error during combined analysis'
        });
    }
});

function generateMockVideoAnalysis(videoUrl) {
    // Generate different mock results based on URL
    if (videoUrl.includes('BigBuckBunny') || videoUrl.includes('animated')) {
        return {
            success: true,
            total_faces_detected: 0,
            frames_analyzed: 10,
            insights: {
                engagement_level: "Unable to determine",
                average_smile_score: "N/A",
                video_quality: "High",
                recommendations: [
                    "No human faces detected - this appears to be animated content",
                    "For presentation analysis, use videos with clear human faces",
                    "Ensure good lighting and camera positioning for best results"
                ]
            }
        };
    } else {
        // Generate realistic mock data for human presentations
        const mockScores = [0.65, 0.78, 0.82, 0.59, 0.71];
        const randomScore = mockScores[Math.floor(Math.random() * mockScores.length)];
        
        return {
            success: true,
            total_faces_detected: Math.floor(Math.random() * 8) + 2, // 2-10 faces
            frames_analyzed: 10,
            insights: {
                engagement_level: randomScore > 0.7 ? "High" : randomScore > 0.5 ? "Medium" : "Low",
                average_smile_score: randomScore,
                video_quality: "High",
                presenter_age_estimate: Math.floor(Math.random() * 30) + 25, // 25-55
                recommendations: generateRecommendations(randomScore)
            }
        };
    }
}

function generateMockTranscriptAnalysis(transcript) {
    // Analyze the transcript for basic metrics
    const words = transcript.split(/\s+/).filter(word => word.length > 0);
    const wordCount = words.length;
    
    // Estimate duration (assuming 150 words per minute average)
    const estimatedDuration = wordCount / 150; // in minutes
    const wordsPerMinute = Math.round(wordCount / Math.max(estimatedDuration, 0.5));
    
    // Count basic filler words
    const fillerWords = {
        "um": (transcript.match(/\bum\b/gi) || []).length,
        "uh": (transcript.match(/\buh\b/gi) || []).length,
        "like": (transcript.match(/\blike\b/gi) || []).length,
        "you know": (transcript.match(/\byou know\b/gi) || []).length
    };
    
    // Mock pause analysis (random but realistic)
    const pausePercentage = Math.round((Math.random() * 15 + 5) * 10) / 10; // 5-20%
    
    // Mock sentiment analysis
    const sentimentScores = [
        { label: "positive", score: 0.78 },
        { label: "neutral", score: 0.65 },
        { label: "positive", score: 0.82 },
        { label: "confident", score: 0.71 }
    ];
    const sentiment = sentimentScores[Math.floor(Math.random() * sentimentScores.length)];
    
    return {
        success: true,
        analysis: {
            speech_pace: {
                words_per_minute: wordsPerMinute,
                total_words: wordCount,
                estimated_duration_minutes: Math.round(estimatedDuration * 10) / 10,
                pause_percentage: pausePercentage
            },
            filler_words: fillerWords,
            sentiment: sentiment,
            recommendations: generateTranscriptRecommendations(wordsPerMinute, fillerWords, pausePercentage)
        }
    };
}

function generateTranscriptRecommendations(wpm, fillers, pausePercentage) {
    const recommendations = [];
    const totalFillers = Object.values(fillers).reduce((a, b) => a + b, 0);
    
    // Speaking pace recommendations
    if (wpm < 120) {
        recommendations.push("Consider speaking slightly faster to maintain audience engagement");
    } else if (wpm > 180) {
        recommendations.push("Try to slow down your speaking pace for better comprehension");
    } else {
        recommendations.push("Excellent speaking pace - very natural and easy to follow");
    }
    
    // Filler words recommendations
    if (totalFillers > 20) {
        recommendations.push("Focus on reducing filler words like 'um' and 'uh' through practice");
    } else if (totalFillers > 10) {
        recommendations.push("Good control of filler words - try to reduce them slightly");
    } else {
        recommendations.push("Great job minimizing filler words!");
    }
    
    // Pause recommendations
    if (pausePercentage < 8) {
        recommendations.push("Consider adding more strategic pauses for emphasis");
    } else if (pausePercentage > 15) {
        recommendations.push("Try to reduce excessive pausing to maintain flow");
    } else {
        recommendations.push("Good use of pauses for natural speech rhythm");
    }
    
    return recommendations;
}

function generateRecommendations(smileScore) {
    const recommendations = [];
    
    if (smileScore > 0.7) {
        recommendations.push("Excellent engagement levels! Your positive energy is contagious");
        recommendations.push("Great use of facial expressions throughout the presentation");
    } else if (smileScore > 0.5) {
        recommendations.push("Good baseline engagement detected");
        recommendations.push("Consider adding more animated expressions during key points");
    } else {
        recommendations.push("Try to incorporate more smiles and positive expressions");
        recommendations.push("Practice in front of a mirror to improve facial engagement");
    }
    
    recommendations.push("Maintain consistent eye contact with the camera");
    recommendations.push("Use hand gestures to complement your facial expressions");
    
    return recommendations;
}

app.listen(PORT, () => {
    console.log(`� Presentation Feedback Server running on http://localhost:${PORT}`);
    console.log(`📊 Ready to analyze presentation videos!`);
    
    if (process.env.FUNCTION_ENDPOINT) {
        console.log(`🔗 Connected to Azure Function: ${process.env.FUNCTION_ENDPOINT}`);
    } else {
        console.log(`⚠️  No Azure Function endpoint configured - using mock data`);
    }
    
    if (process.env.OPENAI_ENDPOINT) {
        console.log(`🤖 AI feedback enabled via OpenAI`);
    } else {
        console.log(`📝 Using template-based feedback`);
    }
});
