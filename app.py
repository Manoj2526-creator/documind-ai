import streamlit as st
import base64
import difflib
from supabase import create_client

# =========================
# 🔐 CONFIG (CHANGE THIS)
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
# 📤 UPLOAD FILE
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
            {"upsert": "true"}   # IMPORTANT FIX
        )
        return True
    except Exception as e:
        st.error(f"Upload error: {file.name}")
        return False

if uploaded_files:
    for file in uploaded_files:
        upload_file(file)

# =========================
# 📂 LOAD FILES FROM SUPABASE
# =========================
file_map = {}

try:
    files = supabase.storage.from_(BUCKET).list()

    for f in files:
        name = f["name"]
        url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{name}"

        import requests
        res = requests.get(url)

        if res.status_code == 200:
            file_map[name] = res.content

    if file_map:
        st.success(f"📁 Loaded {len(file_map)} documents")

except Exception as e:
    st.error("⚠️ Error loading files")

# =========================
# 🔍 SMART SEARCH
# =========================
def smart_search(query, filenames):
    query = query.lower().strip()

    # partial match
    direct = [f for f in filenames if query in f.lower()]

    # fuzzy match
    fuzzy = difflib.get_close_matches(query, filenames, n=5, cutoff=0.3)

    # word match
    words = query.split()
    word_match = [
        f for f in filenames
        if any(w in f.lower() for w in words)
    ]

    return list(set(direct + fuzzy + word_match))

# =========================
# 🔎 SEARCH UI
# =========================
query = st.text_input("🔍 Search your document")

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
# 👁 VIEW PDF
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
