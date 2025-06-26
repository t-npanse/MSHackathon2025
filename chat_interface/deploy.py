from azure.ai.foundry import AIFoundryClient
from azure.identity import DefaultAzureCredential

# Initialize client
credential = DefaultAzureCredential()
client = AIFoundryClient(
    credential=credential,
    subscription_id="your-subscription-id",
    resource_group="your-rg"
)

# Deploy web app
deployment = client.deployments.create_or_update(
    project_name="presentation-feedback-project",
    deployment_name="feedback-chat-app",
    deployment_config={
        "type": "WebApp",
        "source": {
            "path": "./chat_interface",
            "type": "local"
        },
        "environment": {
            "FUNCTION_ENDPOINT": "https://your-function-app.azurewebsites.net/api/analyze_video",
            "OPENAI_ENDPOINT": "your-openai-endpoint",
            "OPENAI_API_KEY": "your-openai-key"
        }
    }
)

print(f"Deployed at: {deployment.endpoint_url}")
