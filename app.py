import streamlit as st
import tempfile
import base64

from supabase import create_client
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# =========================
# 🔐 SUPABASE CONFIG
# =========================
SUPABASE_URL = "https://sfaehfajojbjfaxzfmqu.supabase.co"
SUPABASE_KEY = "sb_publishable_Uel1XdBIV2dLeZj8LBgcbQ_g0-A770T"  # <-- paste your key here

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# MUST match your bucket name exactly (lowercase)
BUCKET = "documents"

# =========================
# 🎨 UI
# =========================
st.set_page_config(page_title="DocuMind AI", layout="wide")
st.title("📄 DocuMind AI")
st.caption("Upload once • Search anytime • View instantly")

# =========================
# 📄 PDF VIEW (SAFE)
# =========================
def display_pdf(file_bytes, file_name):
    st.download_button(
        label=f"📥 Download {file_name}",
        data=file_bytes,
        file_name=file_name,
        mime="application/pdf",
    )

    # Safe preview for smaller PDFs (< 2MB)
    if len(file_bytes) < 2_000_000:
        b64 = base64.b64encode(file_bytes).decode("utf-8")
        html = f"""
        <iframe src="data:application/pdf;base64,{b64}"
        width="100%" height="500px"></iframe>
        """
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("Preview disabled for large file. Use download to view.")

# =========================
# ☁️ SUPABASE HELPERS
# =========================
def upload_file(file):
    try:
        supabase.storage.from_(BUCKET).upload(
            file.name,
            file.getvalue(),
            {"upsert": "true"},  # must be string
        )
        st.success(f"✅ Uploaded: {file.name}")
    except Exception as e:
        st.error(f"❌ Upload error: {file.name}")
        st.write(e)

def list_files():
    try:
        return supabase.storage.from_(BUCKET).list()
    except:
        return []

def download_file(name):
    try:
        return supabase.storage.from_(BUCKET).download(name)
    except:
        return None

# =========================
# 📤 UPLOAD
# =========================
uploaded_files = st.file_uploader(
    "📤 Upload your documents",
    type=["pdf"],
    accept_multiple_files=True,
)

if uploaded_files:
    for f in uploaded_files:
        upload_file(f)

# =========================
# 📂 LOAD FILES
# =========================
saved_files = list_files()
file_map = {}

for f in saved_files:
    name = f.get("name")
    if not name:
        continue
    fb = download_file(name)
    if fb:
        file_map[name] = fb

if file_map:
    st.success(f"📂 Loaded {len(file_map)} documents")
else:
    st.info("Upload documents to begin")

# =========================
# 🧠 BUILD VECTOR DB (AI)
# =========================
@st.cache_resource
def build_db(file_map):
    docs = []
    for name, file_bytes in file_map.items():
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(file_bytes)
                path = tmp.name

            loader = PyPDFLoader(path)
            pages = loader.load()

            for p in pages:
                p.metadata["source"] = name

            docs.extend(pages)
        except:
            st.warning(f"⚠️ Error reading {name}")

    if not docs:
        return None

    embeddings = HuggingFaceEmbeddings()
    return FAISS.from_documents(docs, embeddings)

db = build_db(file_map) if file_map else None

# =========================
# 🔍 SEARCH (IMPROVED)
# =========================
query = st.text_input("🔍 Search your document")

if query and file_map:
    q = query.lower().strip()

    # 1️⃣ Filename matches (show ALL matches)
    matches = [n for n in file_map if q in n.lower()]

    if matches:
        st.success(f"📄 Found {len(matches)} file(s) by name")
        for name in matches:
            with st.expander(name, expanded=(len(matches) == 1)):
                display_pdf(file_map[name], name)

    # 2️⃣ AI fallback (only if no filename match)
    elif db:
        results = db.similarity_search(q, k=3)

        if results:
            # Collect unique file names from top results
            seen = []
            for r in results:
                src = r.metadata.get("source")
                if src and src not in seen:
                    seen.append(src)

            st.warning("⚠️ No exact filename match. Showing closest results:")
            for name in seen:
                with st.expander(name, expanded=(len(seen) == 1)):
                    display_pdf(file_map[name], name)
        else:
            st.error("❌ No document found")
