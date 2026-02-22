import json
from pathlib import Path

# Try to import providers (they should be installed via uv)
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    from google import genai
except ImportError:
    genai = None

from google.oauth2.credentials import Credentials

CREDENTIALS_FILE = Path(__file__).parent.parent / "settings" / "ai_credentials.json"

ORGANIZE_PROMPT = """
You are an expert manuscript editor and book outliner. The user will provide a raw, disorganized draft or wall of text.
Your task is to transform this text into a clean, well-structured Markdown document suitable for a book layout.

Follow these strict rules:
1. Divide the text into logical, readable paragraphs.
2. Group related paragraphs and invent an appropriate, engaging Markdown Heading 2 (##) for each group.
3. If there is a highly actionable piece of advice, an important warning, or an insightful quote, extract it and format it as a markdown blockquote starting with `> [Tip]`, `> [Warning]`, or just `>` for a quote.
4. Correct obvious typos and grammatical errors, but maintain the author's original tone and voice.
5. DO NOT add any conversational filler like "Here is the organized text". Just output the Markdown.
"""

DRAFT_PROMPT = """
You are an expert ghostwriter and book outliner.
The user will provide you with a Book Title, and optionally a Subtitle and Header keyword.
Your task is to generate a highly structured, well-thought-out BOOK DRAFT (at least 3-4 sections) covering this topic.

Follow these strict rules:
1. Start with a `# ` Main Title (using the user's title & subtitle).
2. Create a brief Introduction section.
3. Generate several Markdown Heading 2 (`## `) and Heading 3 (`### `) sections exploring the logical flow of the topic.
4. Within each section, write 2-3 substantial paragraphs of placeholder content or actual drafted content based on your knowledge of the topic.
5. Include at least one `> [Tip]` or `> [Insight]` blockquote in each major section.
6. DO NOT add conversational filler like "Here is your draft:". Output ONLY the Markdown document.
"""

def get_credentials() -> dict:
    if CREDENTIALS_FILE.exists():
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def organize_text(raw_text: str) -> str:
    """
    Reads user credentials, selects the appropriate provider,
    and calls the LLM to organize the text.
    Returns the formatted Markdown string.
    Raises Exception on failure or missing credentials.
    """
    creds = get_credentials()
    provider = creds.get("provider", "")

    if "OpenAI" in provider:
        return _call_openai(creds.get("openai_key"), raw_text, ORGANIZE_PROMPT)
    elif "Anthropic" in provider:
        return _call_anthropic(creds.get("claude_key"), raw_text, ORGANIZE_PROMPT)
    elif "Google" in provider:
        return _call_gemini(creds.get("gemini_key"), creds.get("gemini_token"), raw_text, ORGANIZE_PROMPT)
    else:
        raise ValueError("선택된 AI 모델이 없거나 설정이 올바르지 않습니다. [설정] 창을 확인해주세요.")

def generate_draft(title: str, subtitle: str, header: str) -> str:
    """
    Generates a draft outline/content based on metadata.
    """
    creds = get_credentials()
    provider = creds.get("provider", "")
    
    prompt_text = f"Title: {title}\n"
    if subtitle: prompt_text += f"Subtitle: {subtitle}\n"
    if header: prompt_text += f"Key Theme (Header): {header}\n"

    if "OpenAI" in provider:
        return _call_openai(creds.get("openai_key"), prompt_text, DRAFT_PROMPT)
    elif "Anthropic" in provider:
        return _call_anthropic(creds.get("claude_key"), prompt_text, DRAFT_PROMPT)
    elif "Google" in provider:
        return _call_gemini(creds.get("gemini_key"), creds.get("gemini_token"), prompt_text, DRAFT_PROMPT)
    else:
        raise ValueError("선택된 AI 모델이 없거나 설정이 올바르지 않습니다. [설정] 창을 확인해주세요.")

def _call_openai(api_key: str, raw_text: str, system_prompt: str = ORGANIZE_PROMPT) -> str:
    if not OpenAI:
        raise ImportError("openai 패키지가 설치되지 않았습니다.")
    if not api_key:
        raise ValueError("OpenAI API Key가 설정되지 않았습니다.")
    
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": raw_text}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

def _call_anthropic(api_key: str, raw_text: str, system_prompt: str = ORGANIZE_PROMPT) -> str:
    if not Anthropic:
        raise ImportError("anthropic 패키지가 설치되지 않았습니다.")
    if not api_key:
        raise ValueError("Anthropic API Key가 설정되지 않았습니다.")
    
    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=2048,
        system=system_prompt,
        messages=[
            {"role": "user", "content": raw_text}
        ],
        temperature=0.7
    )
    return response.content[0].text

def _call_gemini(api_key: str, token_info: dict, raw_text: str, system_prompt: str = ORGANIZE_PROMPT) -> str:
    if not genai:
        raise ImportError("google-genai 패키지가 설치되지 않았습니다.")
    
    if api_key:
        client = genai.Client(api_key=api_key)
    elif token_info:
        creds = Credentials(
            token=token_info['token'],
            refresh_token=token_info['refresh_token'],
            token_uri=token_info['token_uri'],
            client_id=token_info['client_id'],
            client_secret=token_info['client_secret'],
            scopes=token_info['scopes']
        )
        client = genai.Client(credentials=creds)
    else:
        raise ValueError("Gemini API Key가 설정되지 않았거나 Google OAuth 로그인이 필요합니다. [설정] 창을 확인해주세요.")
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=raw_text,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
        )
    )
    return response.text
