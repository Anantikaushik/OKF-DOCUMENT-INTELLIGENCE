from __future__ import annotations

import os
import queue
import threading
import time

import streamlit as st

from ingestion.document_manager import DocumentManager
from app.qa.answer_engine import AnswerEngine


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="OKF Document Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 17px;
        color: #666;
        margin-bottom: 30px;
    }

    .status-card {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #ddd;
        margin-bottom: 15px;
    }

    .answer-card {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #ddd;
        margin-top: 10px;
        margin-bottom: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "document_uploaded": False,
    "document_name": None,
    "document_id": None,
    "page_count": 0,
    "input_tokens": 0,
    "output_tokens": 0,
    "total_tokens": 0,
    "last_answer": None,
    "last_sources": [],
    "processing": False,
    "processing_document_id": None,
    "processing_status": [],
    "processing_error": None,
    "processing_complete": False,
    "processing_metadata": None,
    "processing_thread": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def process_document_background(document_id: str, progress_queue: queue.Queue) -> None:
    try:
        document_manager = DocumentManager()
        metadata = document_manager.process_document(
            document_id,
            progress_callback=lambda message: progress_queue.put({"message": message}),
        )
        progress_queue.put({"done": True, "status": "success", "metadata": metadata})
    except Exception as exc:  # pragma: no cover - depends on runtime environment
        progress_queue.put({"done": True, "status": "error", "error": str(exc)})


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🧠 OKF")

    st.markdown("---")

    st.subheader("System")

    st.success("Application Online")

    st.markdown("**Document Engine**")
    st.caption("Docling")

    st.markdown("**Knowledge Graph**")
    st.caption("Neo4j")

    st.markdown("**LLM**")
    st.caption("Groq")

    st.markdown("**Context Optimization**")
    st.caption("Headroom")

    st.markdown("---")

    if st.session_state.document_uploaded:

        st.subheader("Current Document")

        st.write(
            st.session_state.document_name
        )

        st.caption(
            f"Document ID: {st.session_state.document_id}"
        )

        st.caption(
            f"Pages: {st.session_state.page_count}"
        )

    else:

        st.caption("No document loaded.")

    st.markdown("---")

    st.caption("OKF Document Intelligence")


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🧠 OKF Document Intelligence</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Document → Knowledge Graph → Grounded Answers"
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# DOCUMENT UPLOAD
# ============================================================

st.header("📄 Upload Document")

knowledge_graph_enabled = st.checkbox(
    "Enable knowledge graph ingestion (slower)",
    value=os.getenv("ENABLE_KNOWLEDGE_GRAPH_INGESTION", "false").lower() in {"1", "true", "yes", "on"},
    help=(
        "Disable this for faster ingest. "
        "Enable it only if you want Neo4j entity and relationship extraction."
    ),
)
os.environ["ENABLE_KNOWLEDGE_GRAPH_INGESTION"] = str(knowledge_graph_enabled).lower()

uploaded_file = st.file_uploader(
    "Upload a PDF document",
    type=["pdf"],
    help=(
        "Upload a PDF for processing. "
        "The document will be saved and prepared "
        "for the OKF pipeline."
    ),
)


if uploaded_file is not None:

    if st.button(
        "📥 Process Uploaded Document",
        use_container_width=True,
    ):

        try:
            document_manager = DocumentManager()
            file_bytes = uploaded_file.getvalue()
            metadata = document_manager.save_document(
                file_bytes=file_bytes,
                filename=uploaded_file.name,
            )

            progress_queue = queue.Queue()
            thread = threading.Thread(
                target=process_document_background,
                args=(metadata["document_id"], progress_queue),
                daemon=True,
            )

            st.session_state.processing = True
            st.session_state.processing_document_id = metadata["document_id"]
            st.session_state.processing_status = ["Validating and saving document..."]
            st.session_state.processing_error = None
            st.session_state.processing_complete = False
            st.session_state.processing_metadata = None
            st.session_state.processing_thread = thread
            st.session_state.processing_queue = progress_queue
            thread.start()
            st.rerun()

        except Exception as exc:
            st.error(f"Document upload failed: {exc}")

    if st.session_state.processing:
        progress_queue = st.session_state.get("processing_queue")
        thread = st.session_state.get("processing_thread")

        status = st.status("Processing document in the background...", expanded=True)

        while not progress_queue.empty():
            update = progress_queue.get_nowait()
            if update.get("message"):
                st.session_state.processing_status.append(update["message"])
            if update.get("done"):
                st.session_state.processing_complete = True
                st.session_state.processing = False
                st.session_state.processing_metadata = update.get("metadata")
                if update.get("status") == "error":
                    st.session_state.processing_error = update.get("error", "Unknown error")
                else:
                    metadata = update.get("metadata")
                    st.session_state.document_uploaded = True
                    st.session_state.document_name = metadata["filename"]
                    st.session_state.document_id = metadata["document_id"]
                    st.session_state.page_count = metadata["page_count"]

        if thread is not None and thread.is_alive():
            status.write(st.session_state.processing_status[-1] if st.session_state.processing_status else "Processing...")
            time.sleep(0.5)
            st.rerun()
        elif st.session_state.processing_complete:
            if st.session_state.processing_error:
                status.update(label="Document processing failed.", state="error", expanded=True)
                st.error(f"Document processing failed: {st.session_state.processing_error}")
            else:
                metadata = st.session_state.processing_metadata
                status.update(label="Document processing complete.", state="complete", expanded=False)
                st.success("Document uploaded successfully!")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Pages", metadata["page_count"])
                with col2:
                    st.metric("File Size", f"{metadata['file_size_bytes'] / (1024 * 1024):.2f} MB")
                with col3:
                    st.metric("Status", "Ready")
                st.session_state.processing = False
                st.session_state.processing_complete = False
                st.session_state.processing_error = None
                st.session_state.processing_metadata = None
                st.session_state.processing_status = []
                st.session_state.processing_document_id = None
                st.session_state.processing_thread = None
                st.session_state.processing_queue = None


# ============================================================
# PROCESSING PIPELINE
# ============================================================

st.markdown("---")

st.header("⚙️ Document Processing")

col1, col2 = st.columns(2)


with col1:

    st.markdown(
        """
        <div class="status-card">

        <h4>1️⃣ Document Upload</h4>

        Upload the PDF document into the application.

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="status-card">

        <h4>2️⃣ Docling Parsing</h4>

        Convert the PDF into a structured document while
        preserving document and page information.

        </div>
        """,
        unsafe_allow_html=True,
    )


with col2:

    st.markdown(
        """
        <div class="status-card">

        <h4>3️⃣ Knowledge Graph</h4>

        Store document chunks, entities and relationships
        in Neo4j.

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="status-card">

        <h4>4️⃣ Question Answering</h4>

        Retrieve relevant document knowledge and generate
        grounded answers with page citations.

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# CURRENT DOCUMENT STATUS
# ============================================================

st.markdown("---")

st.header("📊 Document Status")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Documents",
        1 if st.session_state.document_uploaded else 0,
    )

with col2:

    st.metric(
        "Pages",
        st.session_state.page_count,
    )

with col3:

    st.metric(
        "Chunks",
        "—",
    )

with col4:

    st.metric(
        "Entities",
        "—",
    )


if st.session_state.document_uploaded:

    st.success(
        f"Document ready: {st.session_state.document_name}"
    )


# ============================================================
# QUESTION AREA
# ============================================================

st.markdown("---")

st.header("💬 Ask Your Document")

question = st.text_input(
    "Ask a question about the uploaded document",
    placeholder="Example: What is PixelRAG?",
)


if st.button(
    "🔎 Ask Question",
    use_container_width=True,
):

    if not st.session_state.document_uploaded:

        st.warning(
            "Please upload a PDF document first."
        )

    elif not question.strip():

        st.warning(
            "Please enter a question."
        )

    else:

        engine = None

        try:

            with st.spinner(
                "Retrieving document context and generating answer..."
            ):

                engine = AnswerEngine()

                result = engine.answer(
                    question=question,
                    document_id=st.session_state.document_id,
                    top_k=5,
                )

            # ------------------------------------------------
            # STORE RESULT
            # ------------------------------------------------

            st.session_state.last_answer = result.get(
                "answer",
                "",
            )

            st.session_state.last_sources = result.get(
                "sources",
                [],
            )

            usage = result.get(
                "usage",
                {},
            )

            st.session_state.input_tokens = usage.get(
                "input_tokens",
                0,
            )

            st.session_state.output_tokens = usage.get(
                "output_tokens",
                0,
            )

            st.session_state.total_tokens = usage.get(
                "total_tokens",
                0,
            )

        except Exception as exc:

            st.error(
                f"Question processing failed: {exc}"
            )

        finally:

            if engine is not None:

                try:
                    engine.close()
                except Exception:
                    pass


# ============================================================
# DISPLAY ANSWER
# ============================================================

if st.session_state.last_answer:

    st.markdown("---")

    st.subheader("📝 Answer")

    st.markdown(
        f"""
        <div class="answer-card">

        {st.session_state.last_answer}

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SOURCES
# ============================================================

if st.session_state.last_sources:

    st.subheader("📚 Sources")

    for source in st.session_state.last_sources:

        page_number = source.get(
            "page_number",
            "Unknown",
        )

        chunk_id = source.get(
            "chunk_id",
            "Unknown",
        )

        st.write(
            f"📄 Page {page_number}  |  Chunk: {chunk_id}"
        )


# ============================================================
# TOKEN USAGE
# ============================================================

st.markdown("---")

st.header("🔢 Token Usage")

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Input Tokens",
        st.session_state.input_tokens,
    )

with col2:

    st.metric(
        "Output Tokens",
        st.session_state.output_tokens,
    )

with col3:

    st.metric(
        "Total Tokens",
        st.session_state.total_tokens,
    )


st.caption(
    "Token usage is reported by the Groq response. "
    "Headroom is available for context optimization."
)