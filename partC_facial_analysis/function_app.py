import azure.functions as func
import json
import logging
import os
import utils
from typing import Dict, Any

app = func.FunctionApp()

@app.function_name(name="analyze_video_content")
@app.route(route="analyze_video", auth_level=func.AuthLevel.ANONYMOUS)
def analyze_video_content(req: func.HttpRequest) -> func.HttpResponse:
    """
    Analyze video content using Azure Content Understanding API
    Returns facial expression insights and visual sentiment analysis
    """
    logging.info('Video content analysis function triggered')
    
    try:
        # Get video URL or file from request
        req_body = req.get_json()
        if not req_body:
            return func.HttpResponse(
                "Request body must contain video URL or file reference",
                status_code=400
            )
        
        video_url = req_body.get('video_url')
        video_file = req_body.get('video_file')
        
        if not video_url and not video_file:
            return func.HttpResponse(
                "Either 'video_url' or 'video_file' must be provided",
                status_code=400
            )
        
        # Analyze video content using Azure Content Understanding
        insights = utils.analyze_video_with_content_understanding(video_url, video_file)
        
        # Generate structured insights for the chat model
        structured_insights = utils.generate_presentation_insights(insights)
        
        return func.HttpResponse(
            json.dumps(structured_insights, indent=2),
            mimetype="application/json",
            status_code=200
        )
        
    except ValueError as ve:
        logging.error(f"Validation error: {str(ve)}")
        return func.HttpResponse(f"Invalid input: {str(ve)}", status_code=400)
    except Exception as e:
        logging.error(f"Error analyzing video content: {str(e)}")
        return func.HttpResponse(
            f"Error processing video: {str(e)}", 
            status_code=500
        )

@app.function_name(name="get_analysis_status")
@app.route(route="analysis_status/{job_id}", auth_level=func.AuthLevel.ANONYMOUS)
def get_analysis_status(req: func.HttpRequest) -> func.HttpResponse:
    """
    Check the status of a video analysis job
    """
    logging.info('Analysis status check triggered')
    
    try:
        job_id = req.route_params.get('job_id')
        if not job_id:
            return func.HttpResponse("Job ID is required", status_code=400)
        
        status = utils.check_analysis_status(job_id)
        
        return func.HttpResponse(
            json.dumps(status, indent=2),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"Error checking analysis status: {str(e)}")
        return func.HttpResponse(
            f"Error checking status: {str(e)}", 
            status_code=500
        )
