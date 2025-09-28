"""
AI Integration Module for VTHAX26 Backend
Handles AI-powered service classification, follow-ups, and provider matching
"""

import asyncio
import json
import httpx
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"

class AIServiceError(Exception):
    """Custom exception for AI service errors"""
    pass

async def call_ollama(prompt: str, model: str = OLLAMA_MODEL) -> str:
    """
    Call Ollama API with the given prompt
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
    except httpx.TimeoutException:
        raise AIServiceError("AI service timeout - please try again")
    except httpx.RequestError as e:
        raise AIServiceError(f"AI service connection error: {str(e)}")
    except Exception as e:
        raise AIServiceError(f"AI service error: {str(e)}")

def classify_service_request(text: str) -> Dict[str, Any]:
    """
    Classify user's service request into specific service categories using AI
    """
    try:
        # Service categories with keywords for classification
        service_categories = {
            "home_cleaning": {
                "name": "Home Cleaning",
                "description": "Professional house cleaning services",
                "keywords": ["clean", "cleaning", "house", "home", "vacuum", "mop", "dust", "tidy", "organize"]
            },
            "plumbing": {
                "name": "Plumbing",
                "description": "Plumbing repairs and installations",
                "keywords": ["plumber", "plumbing", "pipe", "leak", "faucet", "toilet", "drain", "water", "sink"]
            },
            "electrical": {
                "name": "Electrical",
                "description": "Electrical repairs and installations",
                "keywords": ["electrician", "electrical", "wiring", "outlet", "switch", "light", "power", "circuit"]
            },
            "appliance_repair": {
                "name": "Appliance Repair",
                "description": "Home appliance repair services",
                "keywords": ["repair", "fix", "appliance", "broken", "not working", "refrigerator", "washing machine", "ac"]
            },
            "handyman": {
                "name": "Handyman",
                "description": "General handyman services",
                "keywords": ["handyman", "repair", "fix", "install", "mount", "assemble", "build", "maintenance"]
            },
            "gardening": {
                "name": "Gardening",
                "description": "Garden maintenance and landscaping",
                "keywords": ["garden", "gardening", "landscaping", "lawn", "mow", "plant", "tree", "yard"]
            }
        }
        
        # Simple keyword-based classification (can be enhanced with AI)
        text_lower = text.lower()
        best_match = None
        max_score = 0
        
        for service_id, service_info in service_categories.items():
            score = sum(1 for keyword in service_info["keywords"] if keyword in text_lower)
            if score > max_score:
                max_score = score
                best_match = service_id
        
        if best_match:
            return {
                "service_id": best_match,
                "service_name": service_categories[best_match]["name"],
                "confidence": min(max_score / len(service_categories[best_match]["keywords"]), 1.0),
                "description": service_categories[best_match]["description"]
            }
        else:
            return {
                "service_id": "general",
                "service_name": "General Service",
                "confidence": 0.5,
                "description": "General service request"
            }
            
    except Exception as e:
        logger.error(f"Error in service classification: {str(e)}")
        raise AIServiceError(f"Classification failed: {str(e)}")

def get_service_followups(service_id: str, answers: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get follow-up questions for a specific service
    """
    try:
        if answers is None:
            answers = {}
            
        followup_questions = {
            "home_cleaning": [
                "What type of cleaning do you need? (deep clean, regular clean, move-in/out)",
                "How many rooms need cleaning?",
                "Do you have any specific areas of concern?",
                "What's your preferred time for the service?"
            ],
            "plumbing": [
                "What type of plumbing issue are you experiencing?",
                "Is this an emergency or can it wait?",
                "Have you tried any DIY solutions?",
                "When did the problem start?"
            ],
            "electrical": [
                "What electrical work do you need?",
                "Is this related to new construction or existing wiring?",
                "Do you need permits for this work?",
                "What's your timeline for completion?"
            ],
            "appliance_repair": [
                "What appliance needs repair?",
                "What's the make and model?",
                "What symptoms are you experiencing?",
                "How old is the appliance?"
            ],
            "handyman": [
                "What specific tasks do you need help with?",
                "Do you have the necessary materials?",
                "What's your budget range?",
                "When do you need this completed?"
            ],
            "gardening": [
                "What type of gardening work do you need?",
                "What's the size of your garden/yard?",
                "Do you have any specific plant preferences?",
                "How often do you need maintenance?"
            ]
        }
        
        questions = followup_questions.get(service_id, [
            "Can you provide more details about your request?",
            "What's your preferred timeline?",
            "Do you have any specific requirements?"
        ])
        
        return {
            "service_id": service_id,
            "questions": questions,
            "answers": answers,
            "next_step": "provider_matching" if len(answers) >= 2 else "more_questions"
        }
        
    except Exception as e:
        logger.error(f"Error generating followup questions: {str(e)}")
        raise AIServiceError(f"Followup generation failed: {str(e)}")

def match_providers(service_id: str, spec: Dict[str, Any] = None, location: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """
    Match service providers based on service requirements and location
    """
    try:
        if spec is None:
            spec = {}
            
        # Mock provider data (in real app, this would come from database)
        mock_providers = [
            {
                "id": "provider_1",
                "name": "John's Cleaning Service",
                "rating": 4.8,
                "price_range": "$50-100",
                "services": ["home_cleaning"],
                "location": {"lat": 37.7749, "lng": -122.4194},
                "availability": "Available today",
                "experience": "5+ years"
            },
            {
                "id": "provider_2", 
                "name": "Quick Fix Plumbing",
                "rating": 4.6,
                "price_range": "$75-150",
                "services": ["plumbing"],
                "location": {"lat": 37.7849, "lng": -122.4094},
                "availability": "Available tomorrow",
                "experience": "10+ years"
            },
            {
                "id": "provider_3",
                "name": "Spark Electric",
                "rating": 4.9,
                "price_range": "$100-200",
                "services": ["electrical"],
                "location": {"lat": 37.7649, "lng": -122.4294},
                "availability": "Available this week",
                "experience": "8+ years"
            }
        ]
        
        # Filter providers by service type
        matching_providers = [
            p for p in mock_providers 
            if service_id in p["services"]
        ]
        
        # Sort by rating (in real app, would consider location, availability, etc.)
        matching_providers.sort(key=lambda x: x["rating"], reverse=True)
        
        return {
            "service_id": service_id,
            "providers": matching_providers[:5],  # Return top 5 matches
            "total_matches": len(matching_providers),
            "spec": spec,
            "location": location
        }
        
    except Exception as e:
        logger.error(f"Error matching providers: {str(e)}")
        raise AIServiceError(f"Provider matching failed: {str(e)}")

async def test_ai_services():
    """
    Test function to verify AI services are working
    """
    try:
        # Test service classification
        test_text = "I need someone to clean my house this weekend"
        classification = classify_service_request(test_text)
        print(f"Classification test: {classification}")
        
        # Test followup questions
        followups = get_service_followups(classification["service_id"])
        print(f"Followup test: {followups}")
        
        # Test provider matching
        matches = match_providers(classification["service_id"])
        print(f"Matching test: {matches}")
        
        return True
    except Exception as e:
        print(f"AI services test failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Run test when script is executed directly
    asyncio.run(test_ai_services())
