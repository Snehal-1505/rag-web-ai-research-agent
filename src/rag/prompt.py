"""
Prompt Template Construction Module for Haystack AI RAG Application.

Uses Haystack's PromptBuilder component with Jinja2 templating.
"""
from haystack.components.builders import PromptBuilder

# Standard RAG Prompt Template
RAG_PROMPT_TEMPLATE = """You are an AI research assistant.

Answer the user's question using the provided context.

Do not invent facts.

If the answer cannot be found in the provided context, clearly say that the uploaded documents do not contain enough information.

Question:
{{ question }}

Context:
{% for doc in documents %}
Document {{ loop.index }}:
{{ doc.content }}
Source: {{ doc.meta.get('filename', 'Unknown') }} (Page {{ doc.meta.get('page_number', 1) }})
----------------------------------------
{% endfor %}
"""


def get_prompt_builder(template: str = RAG_PROMPT_TEMPLATE) -> PromptBuilder:
    """
    Initializes and returns a Haystack PromptBuilder component.

    Args:
        template: Jinja2 prompt template string.

    Returns:
        PromptBuilder component instance.
    """
    return PromptBuilder(template=template)
