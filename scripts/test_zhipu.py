import sys
import os

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_agents import ai_manager

def test_zhipu():
    print("Testing Zhipu AI Integration...")
    
    # Check if provider is available (likely False without API key)
    if 'zhipu' in ai_manager.providers:
        print("Provider 'zhipu' registered: Yes")
        print(f"Provider 'zhipu' available: {ai_manager.providers['zhipu']['available']}")
        print(f"Provider 'zhipu' models: {ai_manager.providers['zhipu']['models']}")
        
        if ai_manager.providers['zhipu']['available']:
            print("Attempting chat completion...")
            try:
                response = ai_manager.chat_completion(
                    messages=[{"role": "user", "content": "Olá, quem é você?"}],
                    provider="zhipu",
                    model="glm-4"
                )
                print(f"Response: {response}")
            except Exception as e:
                print(f"Error calling Zhipu: {e}")
        else:
            print("Skipping chat completion test (provider unavailable - missing API key?)")
            print("ℹ️  To enable, set ZHIPU_API_KEY in .env")
    else:
        print("❌ Provider 'zhipu' NOT found in AI Manager!")

if __name__ == "__main__":
    test_zhipu()
