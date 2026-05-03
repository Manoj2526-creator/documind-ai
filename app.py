import streamlit as st
import base64
import difflib
import requests
from supabase import create_client

# =========================
# 🔐 CONFIG (EDIT THIS)
# =========================
SUPABASE_URL = "https://sfaehfajojbjfaxzfmqu.supabase.co"
SUPABASE_KEY = "sb_publishable_Uel1XdBIV2dLeZj8LBgcbQ_g0-A770T"  # <-- paste your key here
BUCKET = "documents"  # must be lowercase

# =========================
# 🔌 CONNECT
# =========================
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="DocuMind AI", layout="wide")

# =========================
# 🎨 HEADER
# =========================
st.markdown("""
<h1 style='text-align:center;'>📄 DocuMind AI</h1>
<p style='text-align:center;color:gray;'>Upload once • Search anytime • View instantly</p>
""", unsafe_allow_html=True)

# =========================
# 📤 UPLOAD
# =========================
uploaded_files = st.file_uploader(
    "📤 Upload your documents",
    type=["pdf"],
    accept_multiple_files=True
)

def upload_file(file):
    try:
        supabase.storage.from_(BUCKET).upload(
            file.name,
            file.getvalue(),
            {"upsert": "true"}  # 🔥 IMPORTANT FIX
        )
        return True
    except Exception:
        st.error(f"❌ Upload error: {file.name}")
        return False

if uploaded_files:
    for file in uploaded_files:
        upload_file(file)

# =========================
# 📂 LOAD FILES
# =========================
file_map = {}

try:
    files = supabase.storage.from_(BUCKET).list()

    for f in files:
        name = f["name"]
        url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{name}"

        res = requests.get(url)

        if res.status_code == 200:
            file_map[name] = res.content

    if file_map:
        st.success(f"📁 Loaded {len(file_map)} documents")

except Exception:
    st.error("⚠️ Error loading files")

# =========================
# 🔍 SMART SEARCH (UPGRADED)
# =========================
def normalize(text):
    return "".join(e.lower() for e in text if e.isalnum())

def smart_search(query, filenames):
    query_norm = normalize(query)
    query_words = query.lower().split()

    scored_results = []

    for file in filenames:
        file_lower = file.lower()
        file_norm = normalize(file)

        score = 0

        # Strong match
        if query_norm in file_norm:
            score += 100

        # Word match
        for word in query_words:
            if word in file_lower:
                score += 30

        # Fuzzy similarity
        similarity = difflib.SequenceMatcher(None, query_norm, file_norm).ratio()
        score += similarity * 50

        if score > 20:
            scored_results.append((file, score))

    scored_results.sort(key=lambda x: x[1], reverse=True)

    return [file for file, _ in scored_results]

# =========================
# 🔎 SEARCH UI
# =========================
query = st.text_input("🔍 Search anything (Aadhaar, result, caste...)")

if query and file_map:
    results = smart_search(query, list(file_map.keys()))

    if results:
        st.success(f"📄 Found {len(results)} document(s)")

        for name in results:
            file_bytes = file_map[name]

            st.markdown(f"""
            <div style="
                background:#111827;
                padding:15px;
                border-radius:12px;
                margin-bottom:10px;
                border:1px solid #1f2937;
            ">
                <h4 style="margin:0;">📄 {name}</h4>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                st.download_button(
                    "📥 Download",
                    data=file_bytes,
                    file_name=name,
                    mime="application/pdf",
                    use_container_width=True
                )

            with col2:
                if st.button(f"👁 View", key=name):
                    st.session_state["view_file"] = name

    else:
        st.error("❌ No document found")

# =========================
# 👁 VIEW PDF (MOBILE FIX)
# =========================
if "view_file" in st.session_state:
    name = st.session_state["view_file"]
    file_bytes = file_map[name]

    st.markdown(f"### 📄 Viewing: {name}")

    b64 = base64.b64encode(file_bytes).decode("utf-8")

    st.markdown(f"""
    <iframe src="data:application/pdf;base64,{b64}"
    width="100%" height="700px"
    style="border-radius:10px;"></iframe>
    """, unsafe_allow_html=True)
