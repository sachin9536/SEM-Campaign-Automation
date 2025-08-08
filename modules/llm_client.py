"""
LLM Client Module
Supports multiple LLM providers including OpenAI, Gemini, and local models.
"""

import logging
import os
import json
import time
import requests
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate_response(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """Generate a response from the LLM."""
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini API provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        """
        Initialize Gemini provider.
        
        Args:
            api_key: Google API key
            model: Model to use (default: gemini-1.5-flash)
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.model = model
        self.logger = logging.getLogger(__name__)
        
        if not self.api_key:
            self.logger.warning("No Google API key provided")
            self.client = None
        else:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model)
                self.logger.info(f"Gemini provider initialized with model: {self.model}")
            except ImportError:
                self.logger.error("google-generativeai package not installed")
                self.client = None
            except Exception as e:
                self.logger.error(f"Error initializing Gemini: {e}")
                self.client = None
    
    def generate_response(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """Generate response using Google Gemini API."""
        if not self.client:
            self.logger.warning("Gemini client not available")
            return self._generate_fallback_response(self._prepare_prompt(messages))
        
        try:
            # Convert messages to Gemini format
            prompt = self._prepare_prompt(messages)
            
            # Generate response
            response = self.client.generate_content(
                prompt,
                generation_config={
                    'max_output_tokens': min(max_tokens, 2048),
                    'temperature': temperature,
                }
            )
            
            if response and response.text:
                return response.text.strip()
            else:
                self.logger.warning("Empty response from Gemini")
                return self._generate_fallback_response(prompt)
                
        except Exception as e:
            self.logger.error(f"Error in Gemini API call: {e}")
            return self._generate_fallback_response(self._prepare_prompt(messages))
    
    def _prepare_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to a single prompt string."""
        prompt_parts = []
        
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n".join(prompt_parts) + "\nAssistant:"
    
    def _generate_fallback_response(self, prompt: str) -> str:
        """Generate a fallback response when API is not available."""
        # Simple keyword-based response generation for SEM tasks
        keywords = prompt.lower().split()
        
        # SEM-specific responses based on keywords
        if any(word in keywords for word in ['keyword', 'sem', 'campaign', 'ads']):
            return '{"keywords": ["digital marketing", "online advertising", "search engine optimization", "google ads", "ppc campaigns"], "recommendations": ["Focus on high-intent keywords", "Use exact match for brand terms", "Implement negative keywords"]}'
        elif any(word in keywords for word in ['business', 'service', 'product']):
            return '{"business_type": "digital service provider", "main_services": ["AI solutions", "digital marketing", "web development"], "target_audience": ["small businesses", "startups", "enterprises"], "competitive_advantages": ["AI-powered solutions", "affordable pricing", "expert support"]}'
        elif any(word in keywords for word in ['analysis', 'content', 'website']):
            return '{"business_analysis": {"type": "technology company", "services": ["AI tools", "digital solutions"], "audience": "businesses seeking AI solutions", "advantages": ["innovative technology", "user-friendly interface"]}}'
        elif any(word in keywords for word in ['headline', 'ad', 'copy']):
            return '{"headlines": ["Professional AI Solutions", "Boost Your Business", "Expert Digital Services"], "descriptions": ["Get professional AI solutions for your business. Fast, reliable, and affordable.", "Transform your business with our expert digital services. Contact us today!"]}'
        elif any(word in keywords for word in ['theme', 'category', 'group']):
            return '{"themes": ["AI Solutions", "Digital Marketing", "Business Services"], "categories": ["Technology", "Marketing", "Consulting"], "groups": ["Professional Services", "Technology Solutions", "Business Growth"]}'
        else:
            # Generic response for other queries
            return '{"response": "AI-powered business solutions", "keywords": ["digital", "technology", "business"], "recommendations": ["Focus on core services", "Highlight expertise", "Emphasize value"]}'




class OllamaProvider(LLMProvider):
    """Ollama local provider (completely free, runs locally)."""
    
    def __init__(self, model: str = "llama2", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama provider.
        
        Args:
            model: Model to use (default: llama2)
            base_url: Ollama server URL
        """
        self.model = model
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
    
    def generate_response(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """Generate response using Ollama API."""
        try:
            # Prepare the prompt
            prompt = self._prepare_prompt(messages)
            
            # API endpoint
            url = f"{self.base_url}/api/generate"
            
            # Payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": min(max_tokens, 2048)
                }
            }
            
            # Make request
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                self.logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in Ollama API call: {e}")
            return None
    
    def _prepare_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to a single prompt string."""
        prompt_parts = []
        
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"<|system|>{content}</s>")
            elif role == 'user':
                prompt_parts.append(f"<|user|>{content}</s>")
            elif role == 'assistant':
                prompt_parts.append(f"<|assistant|>{content}</s>")
        
        return "".join(prompt_parts) + "<|assistant|>"


class OpenAIProvider(LLMProvider):
    """OpenAI provider (requires API key and credits)."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
        """
        try:
            from openai import OpenAI
            self.api_key = api_key or os.getenv('OPENAI_API_KEY')
            if self.api_key:
                self.client = OpenAI(api_key=self.api_key)
            else:
                self.client = None
        except ImportError:
            self.client = None
            self.api_key = None
        
        self.logger = logging.getLogger(__name__)
    
    def generate_response(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """Generate response using OpenAI API."""
        if not self.client:
            self.logger.warning("OpenAI client not available")
            return None
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if response and response.choices:
                return response.choices[0].message.content.strip()
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error in OpenAI API call: {e}")
            return None


class LLMClient:
    """Main LLM client that can switch between different providers."""
    
    def __init__(self, provider: str = "auto", **kwargs):
        """
        Initialize LLM client.
        
        Args:
            provider: Provider to use ("openai", "gemini", "ollama", "auto")
            **kwargs: Provider-specific arguments
        """
        self.logger = logging.getLogger(__name__)
        self.provider_name = provider
        self.provider = self._initialize_provider(provider, **kwargs)
    
    def _initialize_provider(self, provider: str, **kwargs) -> Optional[LLMProvider]:
        """Initialize the specified provider."""
        try:
            if provider == "openai":
                return OpenAIProvider(**kwargs)
            elif provider == "gemini":
                return GeminiProvider(**kwargs)
            elif provider == "ollama":
                try:
                    response = requests.get("http://localhost:11434/api/tags", timeout=5)
                    if response.status_code == 200:
                        return OllamaProvider(**kwargs)
                except:
                    pass
                return None
            elif provider == "auto":
                # Priority order: Gemini (reliable) -> Ollama (free) -> OpenAI (paid)
                try:
                    gemini_provider = GeminiProvider(**kwargs)
                    if gemini_provider.client:
                        self.logger.info("Using Gemini provider (reliable)")
                        return gemini_provider
                except Exception as e:
                    self.logger.debug(f"Gemini not available: {e}")
                try:
                    response = requests.get("http://localhost:11434/api/tags", timeout=5)
                    if response.status_code == 200:
                        self.logger.info("Using Ollama provider (free, local)")
                        return OllamaProvider(**kwargs)
                except:
                    self.logger.debug("Ollama not available")
                if os.getenv('OPENAI_API_KEY'):
                    try:
                        openai_provider = OpenAIProvider(**kwargs)
                        if openai_provider.client:
                            self.logger.info("Using OpenAI provider (paid)")
                            return openai_provider
                    except Exception as e:
                        self.logger.debug(f"OpenAI not available: {e}")
                self.logger.warning("No LLM providers available")
                return None
            else:
                self.logger.warning(f"Unknown provider: {provider}")
                return None
        except Exception as e:
            self.logger.error(f"Error initializing provider {provider}: {e}")
            return None
    
    def generate_response(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """Generate response using the configured provider."""
        if not self.provider:
            self.logger.error("No LLM provider available")
            return None
        
        try:
            return self.provider.generate_response(messages, max_tokens, temperature)
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if the LLM provider is available."""
        return self.provider is not None
    
    def get_provider_name(self) -> str:
        """Get the name of the current provider."""
        if isinstance(self.provider, OpenAIProvider):
            return "openai"
        elif isinstance(self.provider, GeminiProvider):
            return "gemini"
        elif isinstance(self.provider, OllamaProvider):
            return "ollama"
        else:
            return "none"
