# Testcase Generator

An automated system for drafting Technical Specifications and generating Test Cases from requirement documents using the power of AI and RAG (Retrieval-Augmented Generation).

---

## System Architecture

The project is built on an event-driven architecture integrated with a RAG pipeline:

1. Document Watchdog: Monitors the `storage/raw_docs` directory. Processing is automatically triggered when new files (.pdf, .md, .txt) are detected.
2. Extraction Service: Powered by LandingAI ADE to extract content from complex documents (especially PDFs with tables) into standardized Markdown.
3. Spec Generation Service: Utilizes Ollama LLMs to transform raw content into professional Technical Specifications (Actors, Functional Requirements, Business Rules).
4. Vector Storage: Uses FAISS to store document chunks, enabling efficient semantic search and context retrieval.
5. Hybrid Search: Combines FAISS vector search with SQLite FTS5 (Full-Text Search) for highly accurate document retrieval.
6. Test Case Generation: Provides an interactive AI chat interface to generate detailed Test Cases based on standardized specs.
7. Excel Export: Automatically exports generated Test Case lists into formatted .xlsx files.

---

## Tech Stack

- Programming Language: Python 3.10+
- AI Framework: LangChain (Classic & Core)
- LLM & Embeddings: Ollama (Qwen series, mxbai-embed-large)
- Document Parsing: LandingAI ADE
- Vector Database: FAISS (CPU version)
- Full-Text Search: SQLite FTS5
- File Monitoring: Watchdog
- Excel Export: openpyxl
- Data Validation: Pydantic v2

---

## Installation & Usage

### 1. Prerequisites

- Install Ollama (https://ollama.com/)
- Pull required models (examples):
  ```bash
  ollama pull qwen2.5:latest
  ollama pull mxbai-embed-large
  ```

### 2. Environment Configuration

Create a `.env` file in the `src/backend/` directory or root as per your config:

```env
LANDING_AI_API_KEY=your_api_key_here
OLLAMA_MODEL=qwen2.5:latest
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Backend

```bash
cd src/backend
python main.py
```

### 5. Workflow

- Place your requirement files (.pdf, .md, .txt) into `storage/raw_docs/`.
- Watch the terminal logs as the system parses the document and drafts the Technical Spec.
- Interact with the AI via terminal chat to ask questions or request Test Case generation.
- Generated Test Cases are automatically exported to `.xlsx` files in the backend directory.

---

## Roadmap

- [x] Project Structure & Package initialization.
- [x] LandingAI ADE & Ollama integration.
- [x] Automated pipeline with Watchdog monitoring.
- [x] Hybrid Search (FAISS + SQLite FTS5).
- [x] Excel Export functionality.
- [ ] REST API development with FastAPI.
- [ ] Web-based User Interface (Frontend).
