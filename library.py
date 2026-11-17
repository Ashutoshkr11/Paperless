import hashlib, hmac, html, os, time, random, threading
from urllib.parse import quote
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from supabase import create_client
from google import genai
from google.genai import types
import markdown as md

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
APP_PASSCODE = os.environ["APP_PASSCODE"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
Llama_API_KEY = os.environ.get("LLAMA_API_KEY", "")
Qwen_API_KEY = os.environ.get("QWEN_API_KEY", "")
BUCKET = "dsanotes"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
gemini = genai.Client(api_key=GEMINI_API_KEY)

_transcription_lock = threading.Lock()

MODEL_PREFERENCE = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
]

def is_rate_limited(error_msg: str) -> bool:
    """Return True when the error is a rate-limit / high-demand error."""
    msg = str(error_msg).lower()
    return any(kw in msg for kw in (
        "high demand", "resource has been exhausted", "rate limit",
        "429", "quota", "too many requests", "service unavailable",
        "internal server error", "deadline exceeded",
    ))

def is_authentication_error(error_msg: str) -> bool:
    """Return True when the error is an authentication/authorization error."""
    msg = str(error_msg).lower()
    return any(kw in msg for kw in (
        "unauthorized", "forbidden", "401", "403", "authentication",
        "invalid api key", "api key expired", "access denied",
    ))

def get_model_client() -> str:
    """Pick the best available flash model for the free tier."""
    env_model = os.environ.get("GEMINI_MODEL")
    if env_model:
        return env_model

    has_gemini_key = bool(GEMINI_API_KEY)
    has_llama_key = bool(Llama_API_KEY)
    has_qwen_key = bool(Qwen_API_KEY)

    try:
        available = []
        for m in gemini.models.list():
            n = m.name.replace("models/", "")
            if "generateContent" in (m.supported_actions or []):
                if "flash" in n and not any(
                    x in n for x in ("image", "tts", "live", "audio", "preview", "exp", "thinking")
                ):
                    available.append(n)
        if available:
            for pref in MODEL_PREFERENCE:
                for m in available:
                    if pref in m:
                        return m
            return sorted(available)[-1]
    except Exception as e:
        print(f"Could not list models ({e}), using default")

    return "gemini-3.5-flash"

GEMINI_MODEL = get_model_client()
print("Using Gemini model:", GEMINI_MODEL)
router = APIRouter()

PROMPT = """You are an expert Data Structures and Algorithms tutor helping a student
prepare for exams. The course language is C.

The image is a photo of class notes or a whiteboard. If it has no readable class
content, output only: No readable notes found.

Otherwise produce Markdown with EXACTLY these sections, in this order:

## Notes
A faithful transcription of the photo, organized with headings and bullet points.
- Keep the teacher's wording, order, definitions and examples.
- Put all code in fenced code blocks tagged c. Keep the code as written. If you
  suspect a bug or typo, leave it and add a comment /* CHECK: reason */.
- Draw diagrams (nodes, pointers, arrows, tables) as simple ASCII, for example
  [10|*]-->[20|*]-->NULL
- Write [unclear] for anything you cannot read. Never guess.
- Add nothing here that is not in the photo.

## Key Points
3 to 6 one-line takeaways worth memorizing.

## Added Explanation (not from the photo)
- Explain the main ideas in simple English.
- Give time and space complexity where relevant.
- If there is code, show a short dry run with small sample values.
- Mention common C mistakes for this topic (NULL checks, pointer handling,
  memory leaks, off-by-one errors).
If the photo is too unclear to explain, write: Not enough content.

## Practice Questions
5 questions in increasing difficulty: definition, dry run or trace, write code,
complexity, and a tricky edge case. Put the answer under each as **Answer:**.

## Flashcards
4 to 6 lines in the form: Question :: Answer

Rules: keep the whole response under about 900 words, and return only the Markdown
with no introduction or closing sentence."""

def _transcribe_with_fallbacks(note_id: int, image_bytes: bytes):
    """Execute transcription with multi-model fallback strategy."""
    transcribe_note(note_id, image_bytes)

    if Llama_API_KEY:
        transcribe_with_llama(note_id, image_bytes)

    if Qwen_API_KEY:
        transcribe_with_qwen(note_id, image_bytes)

def transcribe_note(note_id: int, image_bytes: bytes):
    """Transcribe a photo of notes using Gemini with aggressive retry."""
    with _transcription_lock:
        text = None
        last_error = None
        for attempt in range(8):
            try:
                resp = gemini.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=[types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"), PROMPT],
                )
                text = (resp.text or "").strip()
                if text:
                    break
            except Exception as e:
                last_error = e
                print(f"Transcription attempt {attempt + 1} failed for note {note_id}: {e}")
                if not is_rate_limited(str(e)):
                    break
                delay = min(30 * (2 ** attempt), 300)
                delay += random.uniform(0, 15)
                print(f"  Waiting {delay:.0f}s before retry...")
                time.sleep(delay)

        if text:
            supabase.table("notes").update({"clean_notes": text}).eq("id", note_id).execute()
            print(f"Note {note_id} transcribed successfully.")
        else:
            print(f"Note {note_id} FAILED after all retries: {last_error}")
            supabase.table("notes").update({"clean_notes": None}).eq("id", note_id).execute()

def transcribe_with_llama(note_id: int, image_bytes: bytes):
    """Transcribe a photo of notes using Llama (via Llama API)."""
    import base64
    with _transcription_lock:
        text = None
        last_error = None
        for attempt in range(8):
            try:
                import requests
                img_b64 = base64.b64encode(image_bytes).decode('utf-8')
                headers = {
                    "Authorization": f"Bearer {Llama_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "Llama-4-Maverick-17B-128E-Instruct-FP8",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": PROMPT},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                            ]
                        }
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.7
                }
                resp = requests.post(
                    "https://api.llama.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=120
                )
                resp.raise_for_status()
                data = resp.json()
                text = (data.get("choices", [{}])[0].get("message", {}).get("content", "") or "").strip()
                if text:
                    break
            except Exception as e:
                last_error = e
                print(f"Llama transcription attempt {attempt + 1} failed for note {note_id}: {e}")
                if not is_rate_limited(str(e)):
                    break
                delay = min(30 * (2 ** attempt), 300)
                delay += random.uniform(0, 15)
                print(f"  Waiting {delay:.0f}s before retry...")
                time.sleep(delay)

        if text:
            supabase.table("notes").update({"clean_notes": text}).eq("id", note_id).execute()
            print(f"Note {note_id} transcribed successfully with Llama.")
        else:
            print(f"Llama transcription FAILED after all retries for note {note_id}: {last_error}")
            supabase.table("notes").update({"clean_notes": None}).eq("id", note_id).execute()

def transcribe_with_qwen(note_id: int, image_bytes: bytes):
    """Transcribe a photo of notes using Qwen (via OpenAI-compatible API)."""
    import base64
    with _transcription_lock:
        text = None
        last_error = None
        for attempt in range(8):
            try:
                import requests
                img_b64 = base64.b64encode(image_bytes).decode('utf-8')
                headers = {
                    "Authorization": f"Bearer {Qwen_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "qwen2.5-vl-72b-instruct",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": PROMPT},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                            ]
                        }
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.7
                }
                resp = requests.post(
                    "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
                    headers=headers,
                    json=payload,
                    timeout=120
                )
                resp.raise_for_status()
                data = resp.json()
                text = (data.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "") or "").strip()
                if text:
                    break
            except Exception as e:
                last_error = e
                print(f"Qwen transcription attempt {attempt + 1} failed for note {note_id}: {e}")
                if not is_rate_limited(str(e)):
                    break
                delay = min(30 * (2 ** attempt), 300)
                delay += random.uniform(0, 15)
                print(f"  Waiting {delay:.0f}s before retry...")
                time.sleep(delay)

        if text:
            supabase.table("notes").update({"clean_notes": text}).eq("id", note_id).execute()
            print(f"Note {note_id} transcribed successfully with Qwen.")
        else:
            print(f"Qwen transcription FAILED after all retries for note {note_id}: {last_error}")
            supabase.table("notes").update({"clean_notes": None}).eq("id", note_id).execute()

def authed(request: Request) -> bool:
    """Check if the request has a valid passcode cookie."""
    cookie = request.cookies.get("vault_pass")
    if not cookie:
        return False
    expected = hashlib.sha256(APP_PASSCODE.encode()).hexdigest()
    return hmac.compare_digest(cookie, expected)


def page(title: str, body: str) -> str:
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
  body{{font-family:system-ui,sans-serif;max-width:900px;margin:0 auto;padding:1rem;background:#0b1020;color:#e5e7eb;line-height:1.6}}
  a{{color:#93c5fd}}
  .card{{background:#111a33;border:1px solid #23305a;border-radius:12px;padding:1rem;margin:1rem 0}}
  img{{max-width:100%;border-radius:8px}}
  pre{{background:#0b1226;padding:12px;border-radius:8px;overflow-x:auto}}
  table{{border-collapse:collapse}} td,th{{border:1px solid #334;padding:4px 8px}}
  .muted{{color:#9ca3af;font-size:.9rem}}
  input{{padding:12px;font-size:16px;width:100%;box-sizing:border-box;margin:8px 0}}
  button,.btn{{background:#2563eb;color:#fff;border:0;border-radius:8px;padding:8px 14px;text-decoration:none;font-size:15px;cursor:pointer;display:inline-block}}
  @media print{{body{{background:#fff;color:#000}} .noprint{{display:none}}
    .card{{border:0;background:none;page-break-inside:avoid}} pre{{background:#f3f4f6}} a{{color:#000}}}}
</style></head><body>{body}</body></html>"""

def signed_url(path: str) -> str:
    res = supabase.storage.from_(BUCKET).create_signed_url(path, 3600)
    return res.get("signedURL") or res.get("signedUrl") or ""

def get_notes(topic: str):
    return (supabase.table("notes").select("*").eq("topic", topic)
            .order("created_at").execute().data)

def render(text: str) -> str:
    return md.markdown(text, extensions=["fenced_code", "tables"])

@router.get("/login", response_class=HTMLResponse)
def login_form():
    return page("Login", """<h1>DSA Vault</h1><form method="post" action="/login">
      <input name="passcode" type="password" placeholder="Passcode" required>
      <button type="submit">Open library</button></form>""")

@router.post("/login")
def login(passcode: str = Form(...)):
    expected = hashlib.sha256(APP_PASSCODE.encode()).hexdigest()
    if not hmac.compare_digest(hashlib.sha256(passcode.encode()).hexdigest(), expected):
        return HTMLResponse(page("Login", "<p>Wrong passcode. <a href='/login'>Try again</a></p>"), status_code=401)

    resp = RedirectResponse("/library", status_code=303)
    resp.set_cookie("vault_pass", expected,
                    httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30)
    return resp

@router.get("/library", response_class=HTMLResponse)
def library(request: Request):
    if not authed(request):
        return RedirectResponse("/login", status_code=303)

    rows = supabase.table("notes").select("topic, clean_notes").execute().data
    topics = {}
    for r in rows:
        t = topics.setdefault(r["topic"], {"total": 0, "done": 0})
        t["total"] += 1
        t["done"] += 1 if r["clean_notes"] else 0

    cards = "".join(
        f'<div class="card"><a href="/topic/{quote(t)}"><b>{html.escape(t)}</b></a>'
        f'<div class="muted">{v["total"]} photo(s), {v["done"]} transcribed</div></div>'
        for t, v in sorted(topics.items()))

    body = f'<h1>DSA Vault Library</h1>{cards or "<p>No notes yet.</p>"}<p><a href="/">Upload more</a></p>'
    return page("Library", body)

@router.get("/topic/{topic}", response_class=HTMLResponse)
def topic_page(topic: str, request: Request):
    if not authed(request):
        return RedirectResponse("/login", status_code=303)

    items = []
    for n in get_notes(topic):
        if n["clean_notes"]:
            content = render(n["clean_notes"])
        else:
            content = (f'<p class="muted">Not transcribed yet.</p>'
                       f'<form method="post" action="/retry/{n["id"]}"><button>Transcribe now</button></form>')

        items.append(
            f'<div class="card"><div class="muted">{n["created_at"][:10]} · '
            f'{html.escape(n["uploaded_by"] or "")}</div>'
            f'<details><summary>Show original photo</summary><img src="{signed_url(n["image_path"])}"></details>'
            f'{content}</div>')

    t = quote(topic)
    body = (f'<p><a href="/library">← Library</a></p><h1>{html.escape(topic)}</h1>'
            f'<p><a class="btn" href="/topic/{t}/print" target="_blank">Print / Save as PDF</a> '
            f'<a class="btn" href="/topic/{t}/download.md">Download Markdown</a></p>'
            + ("".join(items) or "<p>No notes for this topic.</p>"))
    return page(topic, body)

@router.post("/retry/{note_id}")
def retry(note_id: int, request: Request):
    if not authed(request):
        return RedirectResponse("/login", status_code=303)

    row = (supabase.table("notes").select("image_path, topic")
           .eq("id", note_id).single().execute().data)

    data = supabase.storage.from_(BUCKET).download(row["image_path"])
    _transcribe_with_fallbacks(note_id, data)

    return RedirectResponse(f"/topic/{quote(row['topic'])}", status_code=303)

@router.get("/topic/{topic}/print", response_class=HTMLResponse)
def topic_print(topic: str, request: Request):
    if not authed(request):
        return RedirectResponse("/login", status_code=303)

    sections = "<hr>".join(render(n["clean_notes"]) for n in get_notes(topic) if n["clean_notes"])
    body = (f'<div class="noprint"><button onclick="window.print()">Print / Save as PDF</button></div>'
            f'<h1>{html.escape(topic)} – Study Notes</h1>{sections or "<p>Nothing transcribed yet.</p>"}')
    return page(f"{topic} Study Notes", body)

@router.get("/topic/{topic}/download.md")
def topic_markdown(topic: str, request: Request):
    if not authed(request):
        return RedirectResponse("/login", status_code=303)

    parts = [f"# {topic}\n"] + [n["clean_notes"] for n in get_notes(topic) if n["clean_notes"]]
    fname = topic.lower().replace(" ", "_")
    return Response("\n\n---\n\n".join(parts), media_type="text/markdown",
                    headers={"Content-Disposition": f'attachment; filename="{fname}.md"'})