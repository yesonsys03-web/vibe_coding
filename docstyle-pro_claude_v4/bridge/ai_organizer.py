import json
from pathlib import Path
from .vault_indexer import query_vault

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
You are an expert manuscript editor and book author. The user will provide a draft, an outline, or a raw wall of text.
Your task is to transform this text into a polished, high-quality Markdown document suitable for a published book.

Follow these strict rules:
1. If the text is just an outline or brief draft, EXPAND it into rich, detailed paragraphs. Add compelling explanations and examples.
2. If the text is a raw wall of text, divide it into logical paragraphs and invent engaging Markdown Headings (`## `).
3. If the text is already well-structured, POLISH the sentences to sound professional, smooth, and engaging.
4. Extract highly actionable advice, important warnings, or insightful quotes and format them as Markdown blockquotes: `> [Tip]`, `> [Warning]`, or just `>`.
5. Correct all typos and grammatical errors, maintaining a professional but accessible tone.
6. DO NOT add any conversational filler like "Here is the revised text". Just output the Markdown.
"""

DRAFT_PROMPT = """
You are an expert ghostwriter and book outliner.
The user will provide you with a Book Title, and optionally a Subtitle, Header keyword, and an existing Table of Contents (Outline).
Your task is to generate a highly structured, well-thought-out BOOK DRAFT covering this topic.

Follow these strict rules:
1. Start with a `# ` Main Title (using the user's title & subtitle).
2. Create a brief Introduction section.
3. If the user provides an existing Outline/TOC, you MUST use those exact headings and structure to write the draft. If no outline is provided, generate several Markdown Heading 2 (`## `) and Heading 3 (`### `) sections exploring the logical flow of the topic.
4. Within each section, write 2-3 substantial paragraphs of placeholder content or actual drafted content based on your knowledge of the topic.
5. Include at least one `> [Tip]` or `> [Insight]` blockquote in each major section.
6. DO NOT add conversational filler like "Here is your draft:". Output ONLY the Markdown document.
"""

TOC_PROMPT = """
You are an expert book outliner and structural editor.
The user will provide you with a Book Title, and optionally a Subtitle and Header keyword.
Your task is to generate ONLY the Table of Contents (Outline) for this book.

Follow these strict rules:
1. Start with a `# ` Main Title.
2. Generate a logical sequence of chapters using Heading 2 (`## `).
3. Under each chapter, use bullet points (`- `) to briefly describe what will be covered in that chapter.
4. DO NOT write paragraphs of content. This is JUST an outline.
5. DO NOT add conversational filler. Output ONLY the Markdown document.
"""

RAG_PROMPT = """
You are a brilliant AI assistant living inside the user's personal Knowledge Vault.
The user is asking a question or requesting ideas based on their accumulated writings.
You will be provided with [RETRIEVED CONTEXT], which contains numbered excerpts [1], [2], etc. from the user's own Markdown files.

Follow these strict rules:
1. Ground your answer PRIMARILY in the provided [RETRIEVED CONTEXT].
2. When you use information from an excerpt, you MUST cite it inline using its number in square brackets, e.g., `[1]`, `[2]`.
3. If the context doesn't contain the answer, you can use your general knowledge, but clearly state that you are doing so.
4. Synthesize the ideas intelligently to give the user new insights, connections, or structural suggestions.
5. Use clean, readable Markdown syntax for your response.
6. Write in the same language the user asks the question in (usually Korean).
"""

GUIDE_PROMPT = """
You are a brilliant AI assistant analyzing a user's local Knowledge Vault.
Based on the provided [CONTEXT] texts, generate EXACTLY 3 highly insightful, short, actionable questions that the user could ask you to gain better understanding, uncover new themes, or overcome a block in their writing.

Rules:
1. Each question must be short (under 30 characters if possible) and extremely relevant.
2. Return ONLY the 3 questions separated by a newline (`\\n`). Do NOT add numbers, bullets, or conversational filler.
3. Write the questions in Korean.
Example output:
주인공의 진짜 동기는 뭘까?
이 파일들 간의 공통된 주제는?
결말을 어떻게 개선할 수 있을까?
"""

INLINE_PROMPTS = {
    "polish": "You are a professional editor. Please refine and polish the user's text to make it sound more professional, engaging, and grammatically perfect. Maintain the original language and tone. OUTPUT ONLY THE REVISED TEXT without any filler.",
    "expand": "You are a creative writer. Elaborate and expand on the user's text. Add more details, vivid descriptions, or logical explanations to make it a rich, complete paragraph. OUTPUT ONLY THE EXPANDED TEXT without any filler.",
    "summarize": "You are an expert summarizer. Condense the user's text into its most essential core message. Make it brief and impactful. OUTPUT ONLY THE SUMMARIZED TEXT without any filler."
}

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
    elif "Groq" in provider:
        mdl = "qwen-2.5-32b" if "Qwen" in provider else "llama-3.3-70b-versatile"
        return _call_groq(creds.get("groq_key"), raw_text, ORGANIZE_PROMPT, model=mdl)
    else:
        raise ValueError("선택된 AI 모델이 없거나 설정이 올바르지 않습니다. [설정] 창을 확인해주세요.")

def generate_draft(title: str, subtitle: str, header: str, toc: str = "") -> str:
    """
    Generates a draft outline/content based on metadata and an optional TOC.
    """
    creds = get_credentials()
    provider = creds.get("provider", "")
    
    prompt_text = f"Title: {title}\n"
    if subtitle: prompt_text += f"Subtitle: {subtitle}\n"
    if header: prompt_text += f"Key Theme (Header): {header}\n"
    if toc: prompt_text += f"\nExisting Outline to Follow:\n{toc}\n"

    if "OpenAI" in provider:
        return _call_openai(creds.get("openai_key"), prompt_text, DRAFT_PROMPT)
    elif "Anthropic" in provider:
        return _call_anthropic(creds.get("claude_key"), prompt_text, DRAFT_PROMPT)
    elif "Google" in provider:
        return _call_gemini(creds.get("gemini_key"), creds.get("gemini_token"), prompt_text, DRAFT_PROMPT)
    elif "Groq" in provider:
        mdl = "qwen-2.5-32b" if "Qwen" in provider else "llama-3.3-70b-versatile"
        return _call_groq(creds.get("groq_key"), prompt_text, DRAFT_PROMPT, model=mdl)
    else:
        raise ValueError("선택된 AI 모델이 없거나 설정이 올바르지 않습니다. [설정] 창을 확인해주세요.")

def generate_toc(title: str, subtitle: str, header: str) -> str:
    """
    Generates a Table of Contents (Outline) based on metadata.
    """
    creds = get_credentials()
    provider = creds.get("provider", "")
    
    prompt_text = f"Title: {title}\n"
    if subtitle: prompt_text += f"Subtitle: {subtitle}\n"
    if header: prompt_text += f"Key Theme (Header): {header}\n"

    if "OpenAI" in provider:
        return _call_openai(creds.get("openai_key"), prompt_text, TOC_PROMPT)
    elif "Anthropic" in provider:
        return _call_anthropic(creds.get("claude_key"), prompt_text, TOC_PROMPT)
    elif "Google" in provider:
        return _call_gemini(creds.get("gemini_key"), creds.get("gemini_token"), prompt_text, TOC_PROMPT)
    elif "Groq" in provider:
        mdl = "qwen-2.5-32b" if "Qwen" in provider else "llama-3.3-70b-versatile"
        return _call_groq(creds.get("groq_key"), prompt_text, TOC_PROMPT, model=mdl)
    else:
        raise ValueError("선택된 AI 모델이 없거나 설정이 올바르지 않습니다. [설정] 창을 확인해주세요.")

def inline_edit(text: str, mode: str) -> str:
    """
    Executes a quick inline AI edit based on the given mode ('polish', 'expand', 'summarize').
    """
    if mode not in INLINE_PROMPTS:
        raise ValueError(f"Unknown mode: {mode}")
        
    creds = get_credentials()
    provider = creds.get("provider", "")
    system_prompt = INLINE_PROMPTS[mode]

    if "OpenAI" in provider:
        return _call_openai(creds.get("openai_key"), text, system_prompt)
    elif "Anthropic" in provider:
        return _call_anthropic(creds.get("claude_key"), text, system_prompt)
    elif "Google" in provider:
        return _call_gemini(creds.get("gemini_key"), creds.get("gemini_token"), text, system_prompt)
    elif "Groq" in provider:
        mdl = "qwen-2.5-32b" if "Qwen" in provider else "llama-3.3-70b-versatile"
        return _call_groq(creds.get("groq_key"), text, system_prompt, model=mdl)
    else:
        raise ValueError("선택된 AI 모델이 없거나 설정이 올바르지 않습니다. [설정] 창을 확인해주세요.")

def chat_with_vault(query_text: str, filter_files: list[str] = None) -> tuple[str, list]:
    """
    RAG-based chat using ChromaDB vectors.
    Returns (answer, contexts)
    """
    creds = get_credentials()
    provider = creds.get("provider", "")
    
    # 1. Query ChromaDB for relevant exact chunks
    # If the user selected specific files, we can afford to retrieve more chunks (e.g. 20) to capture the whole document.
    amount = 20 if filter_files else 5
    results = query_vault(query_text, n_results=amount, filter_files=filter_files)
    
    context_text = ""
    for idx, r in enumerate(results):
        context_text += f"--- [Excerpt {idx+1}] from {r['filename']} ---\n{r['content']}\n\n"
        
    if not context_text.strip():
        context_text = "No relevant context found in the vault."
        
    # 2. Build the final Prompt
    full_prompt = f"User Query: {query_text}\n\nContext blocks:\n{context_text}"
    
    answer = ""
    if "OpenAI" in provider:
        answer = _call_openai(creds.get("openai_key"), full_prompt, RAG_PROMPT)
    elif "Anthropic" in provider:
        answer = _call_anthropic(creds.get("claude_key"), full_prompt, RAG_PROMPT)
    elif "Google" in provider:
        answer = _call_gemini(creds.get("gemini_key"), creds.get("gemini_token"), full_prompt, RAG_PROMPT)
    elif "Groq" in provider:
        mdl = "qwen-2.5-32b" if "Qwen" in provider else "llama-3.3-70b-versatile"
        answer = _call_groq(creds.get("groq_key"), full_prompt, RAG_PROMPT, model=mdl)
    else:
        raise ValueError("선택된 AI 모델이 없거나 설정이 올바르지 않습니다. [설정] 창을 확인해주세요.")
        
    return answer, results

def generate_guide_questions(filter_files: list[str] = None) -> list[str]:
    """
    RAG-based generation of 3 insightful questions based on the current context.
    Returns a list of 3 strings.
    """
    creds = get_credentials()
    provider = creds.get("provider", "")
    
    # Just query somewhat randomly or broadly to get a sense of the selected files
    # Using a generic query since we just want the context chunks
    results = query_vault("주요 내용, 핵심 주제, 등장인물, 갈등, 정보", n_results=3, filter_files=filter_files)
    
    if not results:
        # Fallback if vault is empty
        return [
            "여기에 어떤 글을 쓸 계획인가요?",
            "이 보관함의 주요 목적은 무엇인가요?",
            "새로운 아이디어가 필요하신가요?"
        ]
        
    context_text = ""
    for r in results:
        context_text += f"[{r['filename']}] {r['content'][:300]}...\n\n"
        
    full_prompt = f"[CONTEXT]\n{context_text}"
    
    answer = ""
    try:
        if "OpenAI" in provider:
            answer = _call_openai(creds.get("openai_key"), full_prompt, GUIDE_PROMPT)
        elif "Anthropic" in provider:
            answer = _call_anthropic(creds.get("claude_key"), full_prompt, GUIDE_PROMPT)
        elif "Google" in provider:
            answer = _call_gemini(creds.get("gemini_key"), creds.get("gemini_token"), full_prompt, GUIDE_PROMPT)
        elif "Groq" in provider:
            mdl = "qwen-2.5-32b" if "Qwen" in provider else "llama-3.3-70b-versatile"
            answer = _call_groq(creds.get("groq_key"), full_prompt, GUIDE_PROMPT, model=mdl)
        else:
            raise ValueError()
            
        questions = [q.strip("- 1234567890.[]*") for q in answer.split('\n') if q.strip()]
        return questions[:3] if len(questions) >= 3 else (questions + ["추가 질문 1", "추가 질문 2"])[:3]
    except Exception:
        return ["이 문서의 핵심은?", "등장인물 분석", "문맥 요약하기"]

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

def _call_groq(api_key: str, raw_text: str, system_prompt: str = ORGANIZE_PROMPT, model: str = "llama-3.3-70b-versatile") -> str:
    if not OpenAI:
        raise ImportError("openai 패키지가 설치되지 않았습니다.")
    if not api_key:
        raise ValueError("Groq API Key가 설정되지 않았습니다.")
    
    # Use OpenAI client with Groq base URL
    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    response = client.chat.completions.create(
        model=model,
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
