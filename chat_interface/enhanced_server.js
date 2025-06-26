const express = require('express');
const path = require('path');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname)));

// Serve the enhanced interface
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'enhanced_index.html'));
});

// API proxy endpoint for Azure Function (video analysis)
app.post('/api/analyze', async (req, res) => {
    try {
        const { video_url } = req.body;
        
        if (!video_url) {
            return res.status(400).json({ error: 'Video URL is required' });
        }

        // Forward to your Azure Function
        const functionEndpoint = process.env.AZURE_FUNCTION_ENDPOINT || 'https://your-function-app.azurewebsites.net/api/analyze_video';
        
        const response = await fetch(functionEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ video_url })
        });

        if (!response.ok) {
            throw new Error(`Azure Function error: ${response.statusText}`);
        }

        const insights = await response.json();
        res.json(insights);

    } catch (error) {
        console.error('Analysis error:', error);
        res.status(500).json({ 
            error: 'Analysis failed', 
            message: error.message 
        });
    }
});

// API proxy endpoint for transcript analysis (Part B)
app.post('/api/analyze-transcript', async (req, res) => {
    try {
        const { transcript } = req.body;
        
        if (!transcript) {
            return res.status(400).json({ error: 'Transcript is required' });
        }

        // Forward to Part B Azure Function
        const transcriptEndpoint = process.env.TRANSCRIPT_FUNCTION_ENDPOINT || 'https://your-partb-function-app.azurewebsites.net/api/sentiment_analysis';
        
        const response = await fetch(transcriptEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                text: transcript,
                include_coaching: true 
            })
        });

        if (!response.ok) {
            throw new Error(`Transcript Analysis error: ${response.statusText}`);
        }

        const insights = await response.json();
        res.json(insights);

    } catch (error) {
        console.error('Transcript analysis error:', error);
        res.status(500).json({ 
            error: 'Transcript analysis failed', 
            message: error.message 
        });
    }
});

// OpenAI Chat endpoint
app.post('/api/chat', async (req, res) => {
    try {
        const { message, insights } = req.body;
        
        if (!message) {
            return res.status(400).json({ error: 'Message is required' });
        }

        // Create rich context for AI
        const coaching = insights?.coaching_insights || {};
        const archetype = coaching.speaker_archetype || 'balanced_communicator';
        const stage = coaching.development_stage || 'intermediate';
        const patterns = insights?.visual_sentiment?.emotional_patterns || {};
        const recommendations = insights?.recommendations || [];

        const systemPrompt = `You are an expert presentation coach analyzing a ${archetype} speaker at the ${stage} level.

Key Analysis:
- Emotional Arc: ${patterns.emotional_arc || 'unknown'}
- Visual Engagement: ${insights?.presentation_quality?.visual_engagement || 0}/100
- Strengths: ${coaching.communication_strengths?.join(', ') || 'analyzing...'}
- Growth Areas: ${coaching.growth_opportunities?.join(', ') || 'analyzing...'}

Top 3 Recommendations:
${recommendations.slice(0, 3).map((r, i) => `${i+1}. ${r.category}: ${r.suggestion}`).join('\n')}

Provide personalized, encouraging coaching. Reference their archetype and specific metrics. Be conversational and actionable.`;

        const openaiResponse = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`
            },
            body: JSON.stringify({
                model: 'gpt-4',
                messages: [
                    { role: 'system', content: systemPrompt },
                    { role: 'user', content: message }
                ],
                max_tokens: 500,
                temperature: 0.7
            })
        });

        const data = await openaiResponse.json();
        
        if (data.error) {
            throw new Error(data.error.message);
        }

        res.json({ 
            response: data.choices[0].message.content 
        });

    } catch (error) {
        console.error('Chat error:', error);
        res.status(500).json({ 
            error: 'Chat failed', 
            message: error.message 
        });
    }
});

app.listen(PORT, () => {
    console.log(`🚀 Enhanced Presentation Coach running on http://localhost:${PORT}`);
    console.log(`📊 Features: Advanced emotion analysis, speaker archetypes, personalized coaching`);
});

module.exports = app;
