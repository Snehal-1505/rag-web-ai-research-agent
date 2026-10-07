"""
Gemini LLM Generator Component for Haystack AI Application.

Wraps Google Gemini API via the official `google-genai` SDK into a custom
Haystack 2.x `@component`.
"""
import os
from typing import Dict, Any, Optional, List
from haystack import component
from google import genai
from src.config import GEMINI_API_KEY


@component
class GeminiGenerator:
    """
    Haystack 2.x component for generating text responses using Google Gemini API.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-flash",
    ):
        self.api_key = api_key if api_key is not None else (GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", ""))
        self.model_name = model_name
        self._client = None

        if self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception:
                self._client = None

    @component.output_types(replies=List[str])
    def run(self, prompt: str) -> Dict[str, List[str]]:
        """
        Executes text generation for a given prompt.

        Args:
            prompt: Formatted prompt text string.

        Returns:
            Dict containing generated text responses list in 'replies'.
        """
        if not self.api_key:
            return {
                "replies": [
                    "Gemini API key is missing. Please configure GEMINI_API_KEY in your .env file or UI settings."
                ]
            }

        try:
            if not self._client:
                self._client = genai.Client(api_key=api_key)

            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            
            answer_text = response.text if (response and response.text) else "No response generated."
            return {"replies": [answer_text]}
        except Exception as e:
            return {"replies": [f"Error generating response from Gemini API: {str(e)}"]}
