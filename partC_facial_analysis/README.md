# Part C - Facial Expression Analysis

This Azure Function uses **Azure AI Content Understanding** to analyze presentation videos and extract facial expression insights for feedback generation.

## Features

- **Video Analysis**: Processes video URLs using Azure Content Understanding API
- **Facial Expression Detection**: Identifies emotions, confidence levels, and engagement
- **Custom Field Extraction**: Extracts presentation-specific insights
- **Structured Output**: Returns JSON formatted for chat model consumption

## API Endpoints

### POST `/analyze_video`
Analyzes a video and returns facial expression insights.

**Request Body:**
```json
{
  "video_url": "https://example.com/presentation-video.mp4"
}
```

**Response:**
```json
{
  "facial_analysis": {
    "faces_detected": 1,
    "face_groupings": [...],
    "facial_expressions": {
      "smile_percentage": 35.2,
      "neutral_percentage": 58.8,
      "engaged_percentage": 78.4
    }
  },
  "visual_sentiment": {
    "overall_tone": "positive",
    "confidence_indicators": ["High"],
    "segments": [...]
  },
  "presentation_quality": {
    "visual_engagement": 85,
    "professional_appearance": true,
    "consistency": "good"
  },
  "recommendations": [
    {
      "category": "visual_engagement",
      "suggestion": "Great job maintaining eye contact!",
      "priority": "low"
    }
  ]
}
```

### GET `/analysis_status/{job_id}`
Check the status of a video analysis job (for async operations).

## Environment Variables

Set these in your Azure Function App Settings:

```bash
CONTENT_UNDERSTANDING_ENDPOINT=https://your-ai-foundry-resource.cognitiveservices.azure.com
CONTENT_UNDERSTANDING_KEY=your-api-key
```

## Setup Instructions

### 1. Create Azure AI Foundry Resource
There are **TWO different approaches** - the documentation is confusing about this:

**Approach A: Simple Azure AI Foundry Resource (Recommended for REST API)**
1. Go to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource"
3. Search for "Azure AI services" or "Cognitive Services multi-service"
4. Select **"Azure AI services"** (the multi-service resource)
5. Choose your subscription, resource group, and supported region (`westus`, `swedencentral`, `australiaeast`)
6. Select pricing tier (S0 recommended)
7. Click "Review + Create"

This gives you an endpoint and API key that works with the Content Understanding REST API.

**Approach B: Full AI Foundry Hub + Project (For AI Foundry Portal)**
This is only needed if you want to use the AI Foundry portal interface:
1. Create an AI Foundry Hub
2. Create a hub-based project
3. Use the project for custom analyzers in the portal

**For your REST API use case, use Approach A** - it's simpler and gives you what you need.

### 2. Get Your API Key
After creating the **Azure AI services** resource:

1. **In Azure Portal:**
   - Go to your Azure AI services resource 
   - Click "Keys and Endpoint" in the left menu
   - Copy **Key 1** or **Key 2** 
   - Copy the **Endpoint URL**

2. **Via Azure CLI:**
   ```bash
   # Get the endpoint
   az cognitiveservices account show \
     --name "your-ai-services-resource" \
     --resource-group "your-rg" \
     --query "properties.endpoint"
   
   # Get the API key
   az cognitiveservices account keys list \
     --name "your-ai-services-resource" \
     --resource-group "your-rg" \
     --query "key1"
   ```

**CLI Command for Simple Approach:**
```bash
az cognitiveservices account create \
  --name "your-ai-services" \
  --resource-group "your-rg" \
  --kind "CognitiveServices" \
  --sku "S0" \
  --location "westus"
```

### 3. Deploy Azure Function
### 3. Deploy Azure Function
```bash
cd partC_facial_analysis
func azure functionapp publish your-function-app-name
```

### 4. Set Environment Variables
```bash
az functionapp config appsettings set \
  --name your-function-app-name \
  --resource-group your-rg \
  --settings "CONTENT_UNDERSTANDING_ENDPOINT=https://your-ai-services-resource.cognitiveservices.azure.com"

az functionapp config appsettings set \
  --name your-function-app-name \
  --resource-group your-rg \
  --settings "CONTENT_UNDERSTANDING_KEY=your-api-key"
```

## Important Notes

⚠️ **Resource Type**: You can use either:
- **Simple**: Azure AI services (multi-service) resource ← **Recommended for REST API**
- **Complex**: Full AI Foundry Hub + Project ← Only needed for portal interface

⚠️ **Regions**: Content Understanding is only available in: `westus`, `swedencentral`, `australiaeast`
⚠️ **Preview Service**: This is a preview service - features may change
⚠️ **Hub vs Resource**: The documentation mixes these concepts - for REST API, you just need the resource

## Azure Content Understanding Configuration

The function uses these Azure Content Understanding features:

- **Face Grouping**: Groups faces appearing in video (`enableFace: true`)
- **Face Description**: Describes facial expressions (`disableFaceBlurring: true`)  
- **Custom Fields**: Extracts presentation-specific insights:
  - `emotionDescription`: Emotional state and facial expressions
  - `confidenceLevel`: Overall confidence (Low/Medium/High)
  - `engagementScore`: Visual engagement assessment
  - `presentationQuality`: Overall delivery assessment

## Integration with Chat Model

The insights.json output is designed to be consumed by your AI chat model for generating presentation feedback reports. The structured format includes:

- **Quantitative metrics**: Engagement scores, face detection counts
- **Qualitative assessments**: Emotion descriptions, confidence levels  
- **Actionable recommendations**: Prioritized feedback for improvement
- **Supporting data**: Timestamps, confidence scores, detailed segments

## Testing

Run the test suite:
```bash
python -m pytest tests/test_video_analysis.py -v
```

## Limitations

- **Video Format**: Supports standard video formats (MP4, AVI, MOV)
- **Processing Time**: Large videos may take 5-10 minutes to process
- **Frame Sampling**: ~1 FPS sampling rate for analysis
- **Resolution**: Frames resized to 512x512px for processing

## Usage Example

```python
import requests

# Analyze a presentation video
response = requests.post(
    "https://your-function-app.azurewebsites.net/api/analyze_video",
    json={"video_url": "https://example.com/my-presentation.mp4"}
)

insights = response.json()
print(f"Engagement Score: {insights['presentation_quality']['visual_engagement']}")
print(f"Recommendations: {len(insights['recommendations'])}")
```

## Architecture Integration

This component fits into the larger presentation feedback system:

```
Teams Recording → [Part A: Graph API] → Video URL
                                      ↓
Video URL → [Part C: Facial Analysis] → insights.json
                                      ↓
insights.json → [Chat Model] → Feedback Report
```

The insights.json serves as the bridge between video analysis and report generation.
