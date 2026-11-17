import io, os, uuid
from datetime import datetime
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from PIL import Image, ImageOps
from supabase import create_client
from dotenv import load_dotenv
load_dotenv()
from library import router, _transcribe_with_fallbacks

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
APP_PASSCODE = os.environ["APP_PASSCODE"]
BUCKET = "dsanotes"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
app = FastAPI()
app.include_router(router)

TOPICS = ["Arrays", "Linked List", "Stack", "Queue", "Trees", "Graphs",
          "Sorting", "Searching", "Recursion", "Other"]

PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DSA Vault | Notes Upload</title>

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">

    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 25px;
            font-family: 'Inter', sans-serif;
            color: #f8fafc;
            background:
                radial-gradient(ellipse at 15% 20%, rgba(37,99,235,.22), transparent 45%),
                radial-gradient(ellipse at 85% 80%, rgba(124,58,237,.20), transparent 45%),
                #070b16;
            overflow-x: hidden;
        }

        body::before {
            content: "";
            position: fixed;
            inset: 0;
            background-image:
                linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px);
            background-size: 40px 40px;
            mask-image: linear-gradient(to bottom, black, transparent);
            pointer-events: none;
        }

        .container {
            width: 100%;
            max-width: 470px;
            position: relative;
            z-index: 1;
        }

        .top-label {
            display: flex;
            justify-content: center;
            margin-bottom: 22px;
        }

        .status {
            display: inline-flex;
            align-items: center;
            gap: 9px;
            padding: 8px 15px;
            border: 1px solid rgba(96,165,250,.25);
            border-radius: 30px;
            background: rgba(37,99,235,.08);
            color: #93c5fd;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.5px;
            text-transform: uppercase;
        }

        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #22c55e;
            box-shadow: 0 0 12px #22c55e;
        }

        .card {
            padding: 38px;
            border: 1px solid rgba(148,163,184,.16);
            border-radius: 24px;
            background: rgba(15,23,42,.82);
            backdrop-filter: blur(20px);
            box-shadow:
                0 25px 80px rgba(0,0,0,.45),
                inset 0 1px 0 rgba(255,255,255,.05);
        }

        .logo {
            width: 58px;
            height: 58px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 25px;
            border-radius: 17px;
            font-size: 27px;
            background: linear-gradient(135deg, #2563eb, #7c3aed);
            box-shadow: 0 8px 30px rgba(79,70,229,.35);
        }

        h1 {
            font-size: 29px;
            font-weight: 800;
            letter-spacing: -1.2px;
            margin-bottom: 10px;
        }

        h1 span {
            background: linear-gradient(90deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .subtitle {
            color: #94a3b8;
            font-size: 13px;
            line-height: 1.7;
            margin-bottom: 30px;
        }

        .field {
            margin-bottom: 19px;
        }

        label {
            display: block;
            margin-bottom: 9px;
            color: #cbd5e1;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: .4px;
        }

        input, select {
            width: 100%;
            padding: 15px 16px;
            border: 1px solid #263449;
            border-radius: 11px;
            outline: none;
            background: #0b1424;
            color: #f8fafc;
            font-family: inherit;
            font-size: 13px;
            transition: .25s ease;
        }

        input:focus, select:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59,130,246,.13);
        }

        input::placeholder {
            color: #64748b;
        }

        select {
            cursor: pointer;
            color: #cbd5e1;
        }

        input[type="file"] {
            padding: 14px;
            cursor: pointer;
            font-size: 11px;
            color: #94a3b8;
            border-style: dashed;
            background: #08111f;
        }

        input[type="file"]::file-selector-button {
            border: 0;
            border-radius: 7px;
            padding: 9px 12px;
            margin-right: 12px;
            background: #1e3a8a;
            color: #bfdbfe;
            font-family: inherit;
            font-weight: 600;
            cursor: pointer;
        }

        button {
            width: 100%;
            padding: 16px;
            margin-top: 10px;
            border: 0;
            border-radius: 11px;
            background: linear-gradient(100deg, #2563eb, #7c3aed);
            color: white;
            font-family: inherit;
            font-size: 14px;
            font-weight: 700;
            letter-spacing: .3px;
            cursor: pointer;
            transition: .25s ease;
            box-shadow: 0 8px 25px rgba(79,70,229,.25);
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 30px rgba(79,70,229,.4);
            filter: brightness(1.12);
        }

        button:active {
            transform: scale(.98);
        }

        .secure-note {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 7px;
            margin-top: 23px;
            color: #64748b;
            font-size: 10px;
        }

        .footer {
            text-align: center;
            margin-top: 23px;
            color: #475569;
            font-size: 10px;
            letter-spacing: .5px;
        }

        @media (max-width: 480px) {
            .card {
                padding: 27px 22px;
            }

            h1 {
                font-size: 25px;
            }
        }
    </style>
</head>

<body>
    <main class="container">

        <div class="top-label">
            <div class="status">
                <span class="status-dot"></span>
                DSA KNOWLEDGE PORTAL
            </div>
        </div>

        <section class="card">

            <div class="logo">DV</div>

            <h1>Upload your <span>notes.</span></h1>

            <p class="subtitle">
                Share your class notes with the community.
                Upload your study material and contribute to
                the collective knowledge vault.
            </p>

            <form action="/upload" method="post" enctype="multipart/form-data">

                <div class="field">
                    <label>SECURITY PASSCODE</label>
                    <input
                        name="passcode"
                        type="password"
                        placeholder="Enter your access passcode"
                        required
                    >
                </div>

                <div class="field">
                    <label>CONTRIBUTOR NAME</label>
                    <input
                        name="uploaded_by"
                        type="text"
                        placeholder="Enter your full name"
                        required
                    >
                </div>

                <div class="field">
                    <label>SELECT SUBJECT / TOPIC</label>
                    <select name="topic" required>
                        <option value="" disabled selected>Choose a topic</option>
                        __OPTIONS__
                    </select>
                </div>

                <div class="field">
                    <label>UPLOAD STUDY MATERIAL</label>
                    <input
                        name="files"
                        type="file"
                        accept="image/*"
                        multiple
                        required
                    >
                    <p class="upload-hint">
                        Supported formats: JPG, PNG, WEBP · Multiple images allowed
                    </p>
                </div>

                <button type="submit">
                    ↑ &nbsp; Upload to DSA Vault
                </button>

            </form>

            <div class="secure-note">
                ◈ &nbsp; Secure submission · Your notes matter
            </div>

        </section>

        <div class="footer">
            DSA VAULT &nbsp;•&nbsp; BUILT FOR LEARNING
        </div>

    </main>
</body>
</html>
"""


def compress(data: bytes) -> bytes:
    img = Image.open(io.BytesIO(data))
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((1600, 1600))
    out = io.BytesIO()
    img.save(out, "JPEG", quality=80, optimize=True)
    return out.getvalue()

@app.get("/", response_class=HTMLResponse)
def home():
    options = "".join(f"<option>{t}</option>" for t in TOPICS)
    return PAGE.replace("__OPTIONS__", options)


def result_page(title: str, message: str, error: bool = False) -> str:
    icon = "!" if error else "✓"
    kind = " error" if error else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | DSA Vault</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            min-height: 100vh; display: flex; align-items: center; justify-content: center;
            padding: 25px; font-family: Inter, sans-serif; color: #f8fafc;
            background:
                radial-gradient(ellipse at 15% 20%, rgba(37,99,235,.22), transparent 45%),
                radial-gradient(ellipse at 85% 80%, rgba(124,58,237,.20), transparent 45%),
                #070b16;
        }}
        .card {{
            width: 100%; max-width: 470px; padding: 38px; text-align: center;
            border: 1px solid rgba(148,163,184,.16); border-radius: 24px;
            background: rgba(15,23,42,.82); backdrop-filter: blur(20px);
            box-shadow: 0 25px 80px rgba(0,0,0,.45);
        }}
        .icon {{
            width: 64px; height: 64px; margin: 0 auto 22px; display: flex;
            align-items: center; justify-content: center; border-radius: 18px;
            font-size: 28px; font-weight: 800;
            background: {"linear-gradient(135deg, #b91c1c, #7c2d12)" if error else "linear-gradient(135deg, #2563eb, #7c3aed)"};
        }}
        h1 {{ font-size: 26px; font-weight: 800; letter-spacing: -1px; margin-bottom: 12px; }}
        p {{ color: #94a3b8; font-size: 14px; line-height: 1.7; margin-bottom: 28px; }}
        a {{
            display: block; padding: 16px; border-radius: 11px; text-decoration: none;
            background: linear-gradient(100deg, #2563eb, #7c3aed); color: white; font-weight: 700;
        }}
    </style>
</head>
<body>
    <section class="card{kind}">
        <div class="icon">{icon}</div>
        <h1>{title}</h1>
        <p>{message}</p>
        <a href="/">← Back to upload</a>
    </section>
</body>
</html>"""


@app.post("/upload", response_class=HTMLResponse)
async def upload(
    background_tasks: BackgroundTasks,
    passcode: str = Form(...),
    uploaded_by: str = Form(...),
    topic: str = Form(...),
    files: list[UploadFile] = File(...),
):
    if passcode != APP_PASSCODE:
        return HTMLResponse(
            result_page(
                "Wrong passcode",
                "That access code does not match. Try again from the upload page.",
                error=True,
            ),
            status_code=401,
        )

    slug = topic.lower().replace(" ", "_")
    count = 0

    for f in files:
        data = compress(await f.read())

        path = (
            f"{slug}/{datetime.utcnow():%Y-%m-%d}/"
            f"{uuid.uuid4().hex}.jpg"
        )

        supabase.storage.from_(BUCKET).upload(
            path,
            data,
            {"content-type": "image/jpeg"}
        )

        result = supabase.table("notes").insert({
            "topic": topic,
            "uploaded_by": uploaded_by,
            "image_path": path
        }).execute()

        note_id = result.data[0]["id"]

        background_tasks.add_task(
            _transcribe_with_fallbacks,
            note_id,
            data
        )

        count += 1

    return result_page(
        "Notes uploaded",
        f"{count} photo(s) are in the vault under {topic}. You can add more anytime.",
    )