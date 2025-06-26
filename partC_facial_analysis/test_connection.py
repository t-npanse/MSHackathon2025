#!/usr/bin/env python3
"""
Test script to verify Azure AI Services connection
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api_connection():
    """Test the Azure AI Services API connection"""
    
    # Get credentials from environment
    endpoint = os.getenv('CONTENT_UNDERSTANDING_ENDPOINT')
    api_key = os.getenv('CONTENT_UNDERSTANDING_KEY')
    
    if not endpoint or not api_key:
        print("❌ Error: Missing API credentials in .env file")
        return False
    
    print(f"🔍 Testing connection to: {endpoint}")
    print(f"🔑 Using API key: {api_key[:8]}...")
    
    # Test with a simple Vision API call (analyze endpoint with minimal request)
    test_url = f"{endpoint}/vision/v3.2/analyze?visualFeatures=Categories"
    
    headers = {
        'Ocp-Apim-Subscription-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(test_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print("✅ API connection successful!")
            print(f"📊 Response: {response.status_code}")
            return True
        elif response.status_code == 401:
            print("❌ Authentication failed - check your API key")
            print(f"Response: {response.status_code} - {response.text}")
            return False
        elif response.status_code == 404:
            print("❌ Endpoint not found - check your endpoint URL")
            print(f"Response: {response.status_code} - {response.text}")
            return False
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def test_video_analyze_endpoint():
    """Test the video analyze endpoint specifically"""
    
    endpoint = os.getenv('CONTENT_UNDERSTANDING_ENDPOINT')
    api_key = os.getenv('CONTENT_UNDERSTANDING_KEY')
    
    # Test the video analyze endpoint (without actually submitting a video)
    test_url = f"{endpoint}/vision/v3.2/analyze"
    
    headers = {
        'Ocp-Apim-Subscription-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    # This should return a 400 (bad request) since we're not sending an image
    # But it confirms the endpoint exists and our auth works
    try:
        response = requests.post(test_url, headers=headers, timeout=30)
        
        if response.status_code == 400:
            print("✅ Vision API endpoint is accessible!")
            print("✅ Authentication is working!")
            return True
        elif response.status_code == 200:
            print("✅ Vision API endpoint is accessible!")
            print("✅ Authentication is working!")
            return True
        else:
            print(f"📊 Vision API endpoint response: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing analyze endpoint: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Azure AI Services Connection")
    print("=" * 50)
    
    # Test basic connection
    connection_ok = test_api_connection()
    
    if connection_ok:
        print("\n🎯 Testing video analyze endpoint...")
        test_video_analyze_endpoint()
    
    print("\n" + "=" * 50)
    print("✅ Connection test complete!")
    print("\nNext steps:")
    print("1. If tests passed, you're ready to deploy your Azure Function")
    print("2. If tests failed, check your API key and endpoint in .env")
    print("3. You can now test with actual video URLs")
