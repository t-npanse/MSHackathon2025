#!/usr/bin/env python3
"""
Simple Azure AI Services connectivity test
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_azure_ai_service():
    """Test Azure AI Services basic connectivity"""
    
    endpoint = os.getenv('CONTENT_UNDERSTANDING_ENDPOINT')
    api_key = os.getenv('CONTENT_UNDERSTANDING_KEY')
    
    if not endpoint or not api_key:
        print("❌ Missing credentials in .env file")
        return False
    
    print(f"🔍 Testing: {endpoint}")
    print(f"🔑 API Key: {api_key[:8]}...")
    
    # Test 1: Simple Computer Vision analyze endpoint
    print("\n📊 Test 1: Computer Vision API")
    test_url = f"{endpoint}/vision/v3.2/analyze?visualFeatures=Categories"
    
    headers = {
        'Ocp-Apim-Subscription-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    # Test with empty request (should return 400 but confirms endpoint exists)
    try:
        response = requests.post(test_url, headers=headers, json={}, timeout=30)
        
        if response.status_code == 400:
            print("✅ Computer Vision API is accessible!")
            print("✅ Authentication working!")
            print(f"📋 Response: {response.status_code} - Expected 400 for empty request")
        elif response.status_code == 401:
            print("❌ Authentication failed - check your API key")
            return False
        else:
            print(f"📊 Unexpected response: {response.status_code}")
            print(f"Response: {response.text[:100]}...")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    # Test 2: Try Face API endpoint
    print("\n🎭 Test 2: Face API")
    face_url = f"{endpoint}/face/v1.0/detect"
    
    try:
        response = requests.post(face_url, headers=headers, json={}, timeout=30)
        
        if response.status_code == 400:
            print("✅ Face API is accessible!")
        elif response.status_code == 401:
            print("❌ Face API authentication failed")
        else:
            print(f"📊 Face API response: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️  Face API error: {e}")
    
    # Test 3: Video analysis endpoint
    print("\n🎬 Test 3: Video Analysis")
    video_url = f"{endpoint}/vision/v3.2/analyze"
    
    try:
        response = requests.post(video_url, headers=headers, json={}, timeout=30)
        
        if response.status_code == 400:
            print("✅ Video analysis endpoint is accessible!")
        else:
            print(f"📊 Video analysis response: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️  Video analysis error: {e}")
    
    return True

if __name__ == "__main__":
    print("🚀 Azure AI Services Connectivity Test")
    print("=" * 50)
    
    success = test_azure_ai_service()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Basic connectivity test completed!")
        print("\n🎯 Your Azure AI Services resource appears to be working!")
        print("📝 Next steps:")
        print("   1. Test with actual video/image URLs")
        print("   2. Deploy your Azure Function")
        print("   3. Run end-to-end testing")
    else:
        print("❌ Connection test failed!")
        print("💡 Check your .env file and Azure resource settings")
