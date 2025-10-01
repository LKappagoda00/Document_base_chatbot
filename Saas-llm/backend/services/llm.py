"""
LLM Service for interacting with Ollama (local) or remote LLM APIs.
Supports easy switching between development (local Ollama) and production (remote GPU servers).
"""

import httpx
import json
from typing import Dict, Any, Optional, List
from config.settings import settings


class LLMService:
    """Service for interacting with LLM APIs (Ollama or remote)."""
    
    def __init__(self):
        self.api_url = settings.llm_api_url
        self.model = settings.llm_model
    
    async def query_llm(
        self, 
        prompt: str, 
        context: str = None, 
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Query the LLM with optional context for RAG.
        
        Args:
            prompt: User question/query
            context: Retrieved context from vector DB
            model: Override default model
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum response length
        
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Prepare the full prompt with context
            full_prompt = self._prepare_prompt(prompt, context)
            
            # Use specified model or default
            llm_model = model or self.model
            
            # Make request based on API type (Ollama vs remote)
            if "localhost:11434" in self.api_url or "ollama" in self.api_url.lower():
                return await self._query_ollama(full_prompt, llm_model, temperature)
            else:
                return await self._query_remote_api(full_prompt, llm_model, temperature, max_tokens)
                
        except Exception as e:
            return {
                "response": f"Error: Unable to get response from LLM. {str(e)}",
                "error": True,
                "model": llm_model,
                "prompt_length": len(full_prompt)
            }
    
    async def _query_ollama(self, prompt: str, model: str, temperature: float) -> Dict[str, Any]:
        """Query local Ollama instance."""
        url = f"{self.api_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 2000
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return {
                "response": result.get("response", ""),
                "model": model,
                "done": result.get("done", True),
                "total_duration": result.get("total_duration", 0),
                "prompt_eval_count": result.get("prompt_eval_count", 0),
                "eval_count": result.get("eval_count", 0),
                "error": False
            }
    
    async def _query_remote_api(
        self, 
        prompt: str, 
        model: str, 
        temperature: float, 
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        Query remote LLM API (OpenAI compatible or custom endpoint).
        Adapt this method based on your production LLM API.
        """
        # Example for OpenAI-compatible API
        url = f"{self.api_url}/v1/chat/completions"
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        headers = {
            "Content-Type": "application/json",
            # Add authentication headers for production
            # "Authorization": f"Bearer {os.getenv('LLM_API_KEY')}"
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            # Adapt response format based on your API
            return {
                "response": result["choices"][0]["message"]["content"],
                "model": model,
                "usage": result.get("usage", {}),
                "error": False
            }
    
    def _prepare_prompt(self, query: str, context: str = None) -> str:
        """Prepare the final prompt with context for RAG."""
        if not context:
            return query
        
        # RAG prompt template
        prompt_template = """You are a helpful AI assistant. Use the following context to answer the user's question. If the answer cannot be found in the context, say so clearly.

Context:
{context}

Question: {question}

Answer: """
        
        return prompt_template.format(context=context, question=query)
    
    async def check_model_availability(self, model_name: str = None) -> Dict[str, Any]:
        """Check if a model is available on the LLM service."""
        model_to_check = model_name or self.model
        
        try:
            if "localhost:11434" in self.api_url:
                # Check Ollama models
                url = f"{self.api_url}/api/tags"
                async with httpx.AsyncClient() as client:
                    response = await client.get(url)
                    models = response.json().get("models", [])
                    available_models = [m["name"] for m in models]
                    
                    return {
                        "available": model_to_check in available_models,
                        "model": model_to_check,
                        "all_models": available_models
                    }
            else:
                # For remote APIs, you might need different logic
                return {
                    "available": True,  # Assume available for remote
                    "model": model_to_check,
                    "all_models": [model_to_check]
                }
                
        except Exception as e:
            return {
                "available": False,
                "model": model_to_check,
                "error": str(e)
            }


# Global LLM service instance
llm_service = LLMService()


# Backward compatibility function
async def query_llm(prompt: str, context: str = None, model: str = None) -> str:
    """Backward compatible function for querying LLM."""
    result = await llm_service.query_llm(prompt, context, model)
    return result.get("response", "")
