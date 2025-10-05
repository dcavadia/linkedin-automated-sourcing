import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

USE_OPENAI = os.getenv('USE_OPENAI', 'false').lower() == 'true'

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

if USE_OPENAI and OpenAI:
    client = OpenAI()
else:
    client = None

from app.database import save_message, get_messages_for_candidate

# GPT-2 import and loading (lazy, only if transformers/torch available)
try:
    from transformers import GPT2LMHeadModel, GPT2Tokenizer
    import torch
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    GPT2_AVAILABLE = True
except ImportError:
    tokenizer = None
    model = None
    GPT2_AVAILABLE = False

ROLE_DESCRIPTION = "AI Engineer role at our innovative startup, focusing on ML pipelines and computer vision."


def generate_mock_message(candidate_data: Dict[str, Any]) -> str:
    name = candidate_data.get('name', 'Candidate')
    experience = candidate_data.get('experience', 'experienced AI engineer')
    company = candidate_data.get('current_company', 'a leading tech firm')
    intro = f"Hi {name}, I found your profile impressive, especially your {experience} at {company}."
    role_desc = f"We are hiring for {ROLE_DESCRIPTION} Our team would greatly value your expertise."
    cta = "Please reply if interested in discussing this opportunity further."
    return f"{intro}\n\n{role_desc}\n\n{cta}\n\nBest Regards,\nHiring Team"


def generate_personalized_message_openai(candidate_data: Dict[str, Any]) -> str:
    prompt = f"""
    Generate a personalized LinkedIn outreach message for a job candidate.

    Candidate: {candidate_data.get('name', 'Candidate')}, {candidate_data.get('experience', 'experienced AI engineer')} at {candidate_data.get('current_company', 'a leading tech firm')}.

    Role: {ROLE_DESCRIPTION}

    Structure:
    1. Personalized intro (1-2 sentences based on their experience).
    2. Brief role description (2 sentences).
    3. Clear CTA (e.g., "Reply to discuss opportunities").

    Keep under 150 words, professional, engaging. No spam.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0.7
    )

    return response.choices[0].message.content.strip()


def generate_personalized_message_gpt2(candidate_data: Dict[str, Any]) -> str:
    if not GPT2_AVAILABLE:
        return generate_mock_message(candidate_data)
    name = candidate_data.get('name', 'Candidate')
    experience = candidate_data.get('experience', 'experienced AI engineer')
    company = candidate_data.get('current_company', 'a leading tech firm')
    prompt_text = f"Hi {name}, based on your background in {experience} at {company}, we have an opportunity for you as an AI Engineer."
    inputs = tokenizer.encode(prompt_text, return_tensors='pt')
    outputs = model.generate(inputs, max_length=150, num_return_sequences=1, temperature=0.7, do_sample=True)
    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
    continuation = generated[len(prompt_text):].strip()
    message = f"{prompt_text} {continuation}\n\nBest Regards,\nHiring Team"
    return message


def generate_personalized_message(candidate_data: Dict[str, Any]) -> str:
    if USE_OPENAI and client:
        try:
            return generate_personalized_message_openai(candidate_data)
        except Exception as e:
            print(f"OpenAI generation failed: {e}. Trying GPT-2 fallback.")
    if GPT2_AVAILABLE:
        try:
            return generate_personalized_message_gpt2(candidate_data)
        except Exception as e:
            print(f"GPT-2 generation failed: {e}. Using mock message.")
    return generate_mock_message(candidate_data)


def create_and_save_message(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    message = generate_personalized_message(candidate_data)
    candidate_id = candidate_data['id']
    candidate_name = candidate_data.get('name', 'Unknown Candidate')
    current_company = candidate_data.get('current_company', 'Unknown Company')
    msg_id = save_message(candidate_id, candidate_name, current_company, message)  # Now passes name/company
    return {"id": msg_id, "message": message, "candidate_id": candidate_id}


