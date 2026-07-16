import os
import json
import requests
from config import GROK_API_KEY

def call_grok_api(prompt: str) -> str:
    if not GROK_API_KEY:
        return ""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROK_API_KEY}"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        print(f"Grok API call failed: {e}")
        print(f"Response text: {e.response.text}")
        return ""
    except Exception as e:
        print(f"Grok API call failed: {e}")
        return ""

def generate_disease_explanation(disease_name: str) -> dict:
    """
    Generate detailed agricultural and treatment recommendations for the predicted disease.
    """
    
    if GROK_API_KEY:
        prompt = f'''
        You are an expert agricultural scientist. Provide a highly detailed, comprehensive, and structured analysis 
        for the plant status: "{disease_name}".
        
        CRITICAL INSTRUCTION: If "{disease_name}" indicates that the plant is HEALTHY (e.g., contains the word "healthy"):
        - Write a positive description about the healthy plant.
        - Set ALL arrays (symptoms, causes, chemical, organic, prevention) strictly to ["N/A"].
        - Set ALL strings in the timeline and application_notes strictly to "N/A".
        
        Provide the response strictly in valid JSON format (without markdown block ticks) with the following schema:
        {{
            "disease": (string),
            "description": (string),
            "symptoms": (array of strings),
            "causes": (array of strings),
            "treatment": {{
                "chemical": (array of strings),
                "organic": (array of strings),
                "application_notes": (string)
            }},
            "prevention": (array of strings),
            "timeline": {{
                "day_1_2": (string),
                "day_5_7": (string),
                "ongoing": (string)
            }}
        }}
        Ensure the JSON is strictly valid, with no unescaped quotes inside values or trailing commas.
        Keep the tone informative and highly detailed for an expert farmer.
        '''
        
        try:
            text = call_grok_api(prompt)
            if text:
                text = text.strip()
                if text.startswith('```json'): text = text[7:]
                if text.startswith('```'): text = text[3:]
                if text.endswith('```'): text = text[:-3]
                return json.loads(text.strip())
        except Exception as e:
            print(f"Failed to generate or parse Grok response as JSON: {e}")
            pass

    # Simplified default advice placeholder fallback if API fails or is not set
    is_healthy = "healthy" in disease_name.lower()
    
    if is_healthy:
        return {
            "disease": disease_name,
            "description": "The plant appears to be healthy. (Note: Detailed analysis could not be loaded due to an API limit).",
            "symptoms": ["N/A"],
            "causes": ["N/A"],
            "treatment": {
                "chemical": ["N/A"],
                "organic": ["N/A"],
                "application_notes": "N/A"
            },
            "prevention": ["Continue regular watering and fertilization."],
            "timeline": {
                "day_1_2": "N/A",
                "day_5_7": "N/A",
                "ongoing": "N/A"
            }
        }
    else:
        return {
            "disease": disease_name,
            "description": "Information could not be loaded due to an API error or missing key.",
            "symptoms": ["N/A"],
            "causes": ["N/A"],
            "treatment": {
                "chemical": ["Apply a broad-spectrum copper hydroxide fungicide (Fallback)."],
                "organic": ["Spray organic neem oil (1-2% concentration) (Fallback)."],
                "application_notes": "Apply thoroughly on leaf surfaces."
            },
            "prevention": ["Ensure proper crop rotation and spacing."],
            "timeline": {
                "day_1_2": "Remove infected leaves.",
                "day_5_7": "Monitor for spread.",
                "ongoing": "Expected recovery in 10-14 days."
            }
        }

def chat_with_grok(message: str, history: list, disease_name: str) -> str:
    """
    Continues the conversation about the diagnosed disease using Grok Chat.
    """
    if not GROK_API_KEY:
        return "Sorry, the Agri-Chat feature is currently offline (API key missing)."
        
    try:
        # Convert frontend history format to Grok/OpenAI format
        formatted_history = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "assistant"
            formatted_history.append({"role": role, "content": msg["text"]})
            
        # Add system context if this is the first real question
        if not history:
            context_prompt = f"Act as an expert agricultural assistant. The user just uploaded a leaf diagnosed with '{disease_name}'. Answer their following question concisely and helpfully. IMPORTANT: Always reply in the exact same language that the user uses to ask their question: {message}"
            formatted_history.append({"role": "user", "content": context_prompt})
        else:
            formatted_history.append({"role": "user", "content": message})
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROK_API_KEY}"
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": formatted_history
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        print(f"Grok Chat API call failed: {e}")
        print(f"Response text: {e.response.text}")
        return "I encountered an error while processing your message. Please try again."
    except Exception as e:
        print(f"Grok Chat API call failed: {e}")
        return "I encountered an error while processing your message. Please try again."
