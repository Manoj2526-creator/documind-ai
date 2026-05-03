import base64
import tempfile
import streamlit as st

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

# ⚠️ MUST MATCH YOUR BUCKET NAME EXACTLY
BUCKET = "documents"

# =========================
# 🎨 UI
# =========================
st.set_page_config(page_title="DocuMind AI", layout="wide")
st.title("📄 DocuMind AI")
st.caption("Upload once • Search anytime • View instantly")

# =========================
# 📄 PDF VIEWER
# =========================
def display_pdf(file_bytes):
    base64_pdf = base64.b64encode(file_bytes).decode("utf-8")
    pdf_display = f"""
    <iframe src="data:application/pdf;base64,{base64_pdf}"
    width="100%" height="600px"></iframe>
    """
    st.markdown(pdf_display, unsafe_allow_html=True)

# =========================
# ☁️ SUPABASE FUNCTIONS
# =========================
def upload_file(file):
    try:
        supabase.storage.from_(BUCKET).upload(
            file.name,
            file.getvalue(),
            {"upsert": "true"}   # ✅ FIXED (string, not boolean)
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
# 📤 UPLOAD SECTION
# =========================
uploaded_files = st.file_uploader(
    "📤 Upload your documents",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    for f in uploaded_files:
        upload_file(f)

# =========================
# 📂 LOAD SAVED FILES
# =========================
saved_files = list_files()

file_map = {}

for f in saved_files:
    name = f["name"]
    file_bytes = download_file(name)
    if file_bytes:
        file_map[name] = file_bytes

if file_map:
    st.success(f"📂 Loaded {len(file_map)} saved documents")
else:
    st.info("Upload documents to begin")

# =========================
# 🧠 BUILD AI SEARCH
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
    db = FAISS.from_documents(docs, embeddings)
    return db

db = build_db(file_map) if file_map else None

# =========================
# 🔍 SEARCH
# =========================
query = st.text_input("🔍 Search your document")

if query and file_map:
    query = query.lower()

    # 🔥 1. Filename match
    found = None
    for name in file_map:
        if query in name.lower():
            found = name
            break

    if found:
        st.success(f"📄 Found: {found}")
        file_bytes = file_map[found]

        display_pdf(file_bytes)
        st.download_button("📥 Download", file_bytes, found)

    # 🔥 2. AI search
    elif db:
        results = db.similarity_search(query, k=1)

        if results:
            file_name = results[0].metadata["source"]
            st.success(f"🤖 Found (AI): {file_name}")

            file_bytes = file_map[file_name]
            display_pdf(file_bytes)
            st.download_button("📥 Download", file_bytes, file_name)
        else:
            st.warning("❌ No document found")
