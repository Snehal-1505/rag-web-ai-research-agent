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
        model_name: str = "gemini-3.8-flash",
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
                self._client = genai.Client(api_key=self.api_key)

            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )

            answer_text = response.text if (response and response.text) else "No response generated."
            return {"replies": [answer_text]}
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Gemini API error: {e}", exc_info=True)
            err_str = str(e)
            if "free tier is not available" in err_str or "PERMISSION_DENIED" in err_str:
                return {
                    "replies": [
                        "⚠️ **Gemini API Error (403 Permission Denied)**: The free tier is not enabled for this project. Please enable billing or create a new API key in a project with billing/free quota at [Google AI Studio](https://aistudio.google.com/app/apikey) and update your `.env`."
                    ]
                }
            elif "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                return {
                    "replies": [
                        "⚠️ **Rate Limit Exceeded (429)**: Your Gemini API quota was reached. Please wait a moment before trying again."
                    ]
                }
            return {"replies": ["Something went wrong while generating the answer. Please try again."]}

    def run_stream(self, prompt: str):
        """
        Streams text generation chunks for a given prompt using google-genai streaming.
        Yields string chunks as they arrive.
        """
        if not self.api_key:
            yield "Gemini API key is missing. Please configure GEMINI_API_KEY in your .env file or UI settings."
            return

        try:
            if not self._client:
                self._client = genai.Client(api_key=self.api_key)

            response_stream = self._client.models.generate_content_stream(
                model=self.model_name,
                contents=prompt,
            )
            for chunk in response_stream:
                if chunk and chunk.text:
                    yield chunk.text
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Gemini streaming error: {e}", exc_info=True)
            err_str = str(e)
            if "free tier is not available" in err_str or "PERMISSION_DENIED" in err_str:
                yield "\n\n⚠️ **Gemini API Error (403 Permission Denied)**: The free tier is not enabled for this project. Please enable billing or create a new API key at [Google AI Studio](https://aistudio.google.com/app/apikey) and update `.env`."
            elif "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                yield "\n\n⚠️ **Rate Limit Exceeded (429)**: Gemini quota limit reached. Please wait a moment."
            else:
                yield "\n\nSomething went wrong while generating the answer. Please try again."
