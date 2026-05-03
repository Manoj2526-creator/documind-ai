import os
import base64
import tempfile
import streamlit as st

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# 🎨 PAGE CONFIG
st.set_page_config(page_title="DocuMind AI", layout="wide")

# 🎨 CUSTOM UI
st.markdown("""
<style>
.title {
    font-size: 38px;
    font-weight: bold;
}
.subtitle {
    color: gray;
}
</style>
""", unsafe_allow_html=True)

# 🧭 SIDEBAR
st.sidebar.title("📂 DocuMind AI")
st.sidebar.write("Your Personal Document Assistant")

menu = st.sidebar.radio("Navigation", ["🔍 Search Documents", "ℹ️ About"])

# 📄 PDF DISPLAY FUNCTION
def display_pdf(file_bytes):
    base64_pdf = base64.b64encode(file_bytes).decode("utf-8")
    pdf_display = f"""
    <iframe src="data:application/pdf;base64,{base64_pdf}" 
    width="100%" height="600px" type="application/pdf"></iframe>
    """
    st.markdown(pdf_display, unsafe_allow_html=True)

# 🔍 SEARCH PAGE
if menu == "🔍 Search Documents":

    st.markdown('<p class="title">📄 My AI Document Assistant</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Upload and search your documents instantly</p>', unsafe_allow_html=True)

    # 📤 FILE UPLOAD
    uploaded_files = st.file_uploader(
        "📤 Upload your PDF documents",
        type=["pdf"],
        accept_multiple_files=True
    )

    # 🧠 CREATE DB
    @st.cache_resource
    def create_db(files):
        documents = []

        for file in files:
            try:
                # Save temporarily
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(file.read())
                    tmp_path = tmp.name

                loader = PyPDFLoader(tmp_path)
                docs = loader.load()

                for doc in docs:
                    doc.metadata["source"] = file.name

                documents.extend(docs)

            except:
                st.warning(f"Error reading {file.name}")

        embeddings = HuggingFaceEmbeddings()
        db = FAISS.from_documents(documents, embeddings)
        return db

    if uploaded_files:
        db = create_db(uploaded_files)

        query = st.text_input("🔍 Search your document (e.g., Aadhaar, SSLC, Resume):")

        if query:
            query = query.lower()

            # 🔥 Step 1: Filename match
            found_file = None
            found_bytes = None

            for file in uploaded_files:
                if query in file.name.lower():
                    found_file = file.name
                    found_bytes = file.getvalue()
                    break

            # ✅ If filename match
            if found_file:
                st.success(f"📄 Found (Filename Match): {found_file}")

                display_pdf(found_bytes)

                st.download_button("📥 Download File", found_bytes, found_file)

            # 🔥 Step 2: AI search
            else:
                results = db.similarity_search(query, k=1)

                if results:
                    file_name = results[0].metadata.get("source")

                    st.success(f"📄 Found (AI Match): {file_name}")

                    # find file bytes
                    for file in uploaded_files:
                        if file.name == file_name:
                            file_bytes = file.getvalue()
                            display_pdf(file_bytes)

                            st.download_button("📥 Download File", file_bytes, file_name)
                            break
                else:
                    st.warning("❌ No matching document found")

    else:
        st.info("📤 Upload documents to start")

# ℹ️ ABOUT PAGE
elif menu == "ℹ️ About":

    st.title("ℹ️ About DocuMind AI")

    st.write("""
    **DocuMind AI** is your personal document assistant.

    🔹 Upload and search documents instantly  
    🔹 View PDFs inside the app  
    🔹 Download files easily  
    🔹 Works on mobile and desktop  

    Built using:
    - Python 🐍
    - Streamlit ⚡
    - LangChain 🧠
    - FAISS 🔍
    """)