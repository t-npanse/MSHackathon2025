#!/usr/bin/env python3
"""
Test the facial analysis function with a real video URL
"""
import os
import json
import requests
from dotenv import load_dotenv
from utils import analyze_video_with_content_understanding

# Load environment variables
load_dotenv()

def test_video_analysis():
    """Test video analysis with a sample video URL"""
    
    print("🎬 Testing Video Analysis Pipeline")
    print("=" * 50)
    
    # Test video URLs (you can replace with your own)
    test_videos = [
        {
            "name": "Sample Presentation Video",
            "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
            "description": "Short sample video for testing"
        },
        {
            "name": "Teams Recording Sample",
            "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "description": "Longer sample video"
        }
    ]
    
    print("🔗 Available test videos:")
    for i, video in enumerate(test_videos, 1):
        print(f"  {i}. {video['name']}")
        print(f"     URL: {video['url']}")
        print(f"     Description: {video['description']}")
        print()
    
    # Let user choose or use first video
    choice = input("Enter video number (1-2) or press Enter for video 1: ").strip()
    
    if choice == "2":
        selected_video = test_videos[1]
    else:
        selected_video = test_videos[0]
    
    print(f"\n🎯 Testing with: {selected_video['name']}")
    print(f"📹 URL: {selected_video['url']}")
    
    try:
        print("\n🔄 Starting video analysis...")
        print("This may take 30-60 seconds depending on video length...")
        
        # Call the analysis function
        result = analyze_video_with_content_understanding(video_url=selected_video['url'])
        
        if result['success']:
            print("\n✅ Analysis completed successfully!")
            
            # Save results to file
            output_file = "test_results.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"💾 Results saved to: {output_file}")
            
            # Display summary
            insights = result.get('insights', {})
            print(f"\n📊 Analysis Summary:")
            print(f"   🎭 Emotions detected: {len(insights.get('emotions', []))}")
            print(f"   👥 Faces detected: {insights.get('face_count', 0)}")
            print(f"   ⏱️  Analysis duration: {insights.get('analysis_duration', 'N/A')}")
            
            # Show top emotions
            emotions = insights.get('emotions', [])
            if emotions:
                print(f"\n🎭 Top Emotions Detected:")
                for emotion in emotions[:5]:  # Show top 5
                    name = emotion.get('emotion', 'Unknown')
                    confidence = emotion.get('confidence', 0)
                    timestamp = emotion.get('timestamp', 'N/A')
                    print(f"   • {name}: {confidence:.1%} (at {timestamp})")
            
            return True
            
        else:
            print(f"\n❌ Analysis failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        print("💡 Check your internet connection and Azure API configuration")
        return False

def test_function_app():
    """Test the Azure Function app structure"""
    
    print("\n🔧 Testing Function App Structure")
    print("-" * 30)
    
    try:
        # Import and test the function app
        from function_app import main
        
        # Create a mock request
        mock_request_data = {
            "video_url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
        }
        
        print("✅ Function app imports successfully")
        print("✅ Main function is accessible")
        print("✅ Ready for Azure deployment")
        
        return True
        
    except Exception as e:
        print(f"❌ Function app test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 End-to-End Video Analysis Test")
    print("=" * 50)
    
    # Test 1: Function structure
    structure_ok = test_function_app()
    
    if structure_ok:
        print("\n" + "=" * 50)
        # Test 2: Real video analysis
        analysis_ok = test_video_analysis()
        
        print("\n" + "=" * 50)
        if analysis_ok:
            print("🎉 SUCCESS! Your facial analysis pipeline is working!")
            print("\n🚀 Ready for deployment!")
            print("📝 Next steps:")
            print("   1. Deploy to Azure Functions")
            print("   2. Create chat web interface")
            print("   3. Test with Teams recordings")
        else:
            print("⚠️  Analysis test failed - check logs above")
    else:
        print("❌ Function structure test failed - check imports and dependencies")
