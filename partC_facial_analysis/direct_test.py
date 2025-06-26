#!/usr/bin/env python3
"""
Direct test of video analysis function
"""
import os
import json
from dotenv import load_dotenv
from utils import analyze_video_with_content_understanding

# Load environment variables
load_dotenv()

def test_direct_video_analysis():
    """Test video analysis directly"""
    
    print("🎬 Direct Video Analysis Test")
    print("=" * 40)
    
    # Use a simple, short video for testing
    test_video = "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
    
    print(f"📹 Testing with video: {test_video}")
    print("🔄 Starting analysis (this may take 30-60 seconds)...")
    
    try:
        # Call the analysis function directly
        result = analyze_video_with_content_understanding(video_url=test_video)
        
        print("\n✅ Analysis function called successfully!")
        
        # Save and display results
        with open("direct_test_results.json", "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"💾 Results saved to: direct_test_results.json")
        
        # Show result structure
        print(f"\n📊 Result Structure:")
        print(f"   Keys: {list(result.keys())}")
        print(f"   Success: {result.get('success', 'Unknown')}")
        
        if 'error' in result:
            print(f"   Error: {result['error']}")
        
        if 'insights' in result:
            insights = result['insights']
            print(f"   Insights keys: {list(insights.keys())}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 Testing Video Analysis Function")
    print("=" * 40)
    
    result = test_direct_video_analysis()
    
    print("\n" + "=" * 40)
    if result:
        print("✅ Test completed - check results above")
    else:
        print("❌ Test failed - check error messages above")
