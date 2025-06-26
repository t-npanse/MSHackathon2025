#!/usr/bin/env python3
"""
Test the new face detection video analysis
"""
import os
from dotenv import load_dotenv
from utils_new import analyze_video_with_face_detection
import json

# Load environment variables
load_dotenv()

def test_face_detection_video():
    """Test video analysis with face detection"""
    
    print("🎬 Testing Face Detection Video Analysis")
    print("=" * 50)
    
    # Use a different test video
    test_video = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    
    print(f"📹 Testing with: {test_video}")
    print("🔄 Starting analysis...")
    print("   📥 Downloading video...")
    print("   🎬 Extracting frames...")
    print("   👤 Detecting faces...")
    print("   📊 Generating insights...")
    print()
    
    try:
        result = analyze_video_with_face_detection(video_url=test_video)
        
        # Save results
        with open("face_detection_results.json", "w") as f:
            json.dump(result, f, indent=2)
        
        print("✅ Analysis completed!")
        print(f"💾 Results saved to: face_detection_results.json")
        
        if result.get("success"):
            print(f"\n📊 Results Summary:")
            print(f"   🎭 Total faces detected: {result.get('total_faces_detected', 0)}")
            print(f"   📸 Frames analyzed: {result.get('frames_analyzed', 0)}")
            
            insights = result.get('insights', {})
            print(f"   📈 Engagement level: {insights.get('engagement_level', 'N/A')}")
            print(f"   😊 Average smile score: {insights.get('average_smile_score', 'N/A')}")
            print(f"   🎯 Video quality: {insights.get('video_quality', 'N/A')}")
            
            recommendations = insights.get('recommendations', [])
            if recommendations:
                print(f"\n💡 Recommendations:")
                for rec in recommendations:
                    print(f"   • {rec}")
            
            return True
        else:
            print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Face Detection Video Analysis Test")
    print("=" * 50)
    
    success = test_face_detection_video()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 SUCCESS! Face detection video analysis is working!")
        print("\n🚀 Your presentation feedback system is ready!")
    else:
        print("❌ Test failed - check error messages above")
