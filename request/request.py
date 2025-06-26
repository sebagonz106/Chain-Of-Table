import os
import requests
import json
from typing import Optional, Dict, Any

# Load environment variables from .env file
def _load_env():
    """Load environment variables from .env file if it exists"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load environment variables on import
_load_env()

def ask_llm(initial_query: str, comm: bool = False) -> str:
    """
    Contact an LLM via API to get a response to the given query.
    
    Supports multiple providers in order of preference:
    1. Local Ollama with llama3.2
    2. OpenAI GPT (if OPENAI_API_KEY is set)
    3. Anthropic Claude (if ANTHROPIC_API_KEY is set)
    4. Fallback mock response for testing
    
    Args:
        initial_query: The prompt/query to send to the LLM
        
    Returns:
        str: The LLM's response
        
    Raises:
        Exception: If all LLM providers fail
    """
    
    # Try local Ollama first (primary option)
    try:
        ollama_model = os.getenv('OLLAMA_MODEL', 'llama3.2')
        if(comm): 
            print(f"🦙 Using Ollama with {ollama_model}")
        return _call_ollama(initial_query, ollama_model)
    except Exception as e:
        print(f"Ollama failed: {e}")
    
    # Try OpenAI as fallback
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        try:
            openai_model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
            if(comm): 
                print(f"🤖 Using OpenAI {openai_model}")
            return _call_openai(initial_query, openai_key, openai_model)
        except Exception as e:
            print(f"OpenAI failed: {e}")
    
    # Try Anthropic Claude as second fallback
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    if anthropic_key:
        try:
            anthropic_model = os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307')
            if(comm): 
                print(f"🧠 Using Anthropic {anthropic_model}")
            return _call_anthropic(initial_query, anthropic_key, anthropic_model)
        except Exception as e:
            print(f"Anthropic failed: {e}")
    
    # Fallback for development/testing
    print("⚠️  No LLM providers available")
    return ""


def _call_openai(query: str, api_key: str, model: str = "gpt-3.5-turbo") -> str:
    """Call OpenAI API"""
    url = "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": query}
        ],
        "max_tokens": 2000,
        "temperature": 0.1
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=30)
    response.raise_for_status()
    
    result = response.json()
    return result["choices"][0]["message"]["content"].strip()


def _call_anthropic(query: str, api_key: str, model: str = "claude-3-haiku-20240307") -> str:
    """Call Anthropic Claude API"""
    url = "https://api.anthropic.com/v1/messages"
    
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "max_tokens": 2000,
        "messages": [
            {"role": "user", "content": query}
        ]
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=30)
    response.raise_for_status()
    
    result = response.json()
    return result["content"][0]["text"].strip()


def _call_ollama(query: str, model: str = "llama3.2") -> str:
    """Call local Ollama API"""
    url = "http://localhost:11434/api/generate"
    
    # Optimized parameters for reasoning tasks
    data = {
        "model": model,
        "prompt": query,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature for consistent reasoning
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "num_predict": 2048  # Enough tokens for detailed responses
        }
    }
    
    response = requests.post(url, json=data, timeout=120)  # Increased timeout for local processing
    response.raise_for_status()
    
    result = response.json()
    return result["response"].strip()



# Configuration functions
def set_openai_model(model: str) -> None:
    """Set the OpenAI model to use (e.g., 'gpt-4', 'gpt-3.5-turbo')"""
    global _openai_model
    _openai_model = model

def set_anthropic_model(model: str) -> None:
    """Set the Anthropic model to use (e.g., 'claude-3-opus-20240229')"""
    global _anthropic_model
    _anthropic_model = model

def set_ollama_model(model: str) -> None:
    """Set the Ollama model to use (e.g., 'llama2', 'mistral')"""
    global _ollama_model
    _ollama_model = model

# Global model settings
_openai_model = "gpt-3.5-turbo"
_anthropic_model = "claude-3-haiku-20240307"
_ollama_model = "llama3.2"