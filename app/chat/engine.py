import logging
import math
import os
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from app.chat.schemas import SourceCitation, SuggestedFeedback

logger = logging.getLogger("adhera.chat.engine")

# Medical refusal and emergency trigger keywords
EMERGENCY_TRIGGERS = [
    "chest pain", "can't breathe", "cannot breathe", "shortness of breath",
    "stroke", "facial drooping", "anaphylaxis", "severe allergic",
    "coughing blood", "suicide", "overdose", "unconscious", "heart attack"
]

DIAGNOSIS_TRIGGERS = [
    "diagnose me", "do i have", "what illness do i have", "what disease do i have",
    "could this be cancer", "do you think i have", "am i having a"
]

DOSAGE_CHANGE_TRIGGERS = [
    "should i double", "can i take two pills", "can i stop taking", "can i change my dose",
    "should i stop my medication", "increase my dose", "decrease my dose"
]

DISCLAIMER = "\n\n*This is not medical advice. Consult your healthcare provider.*"


class DocumentChunk:
    def __init__(self, doc_name: str, text: str, chunk_id: int):
        self.doc_name = doc_name
        self.text = text
        self.chunk_id = chunk_id
        self.tokens = self._tokenize(text)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r'\w+', text.lower())


class MedicalRAGEngine:
    """
    Lightweight, deterministic RAG engine engineered for serverless and local execution.
    Loads medical guideline documents, chunks them, performs BM25/cosine semantic retrieval,
    applies clinical safety guardrails, and suggests 1-click side-effect reporting.
    """

    def __init__(self, kb_dir: Optional[str] = None):
        self.kb_dir = kb_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs", "medical_kb")
        self.chunks: List[DocumentChunk] = []
        self.doc_freqs: Counter = Counter()
        self.total_docs: int = 0
        self.avg_doc_len: float = 0.0
        self.ingest_seed_documents()

    def ingest_seed_documents(self) -> Tuple[int, int]:
        """Ingests all markdown and text files from the medical knowledge base directory."""
        if not os.path.exists(self.kb_dir):
            os.makedirs(self.kb_dir, exist_ok=True)

        files = [f for f in os.listdir(self.kb_dir) if f.endswith(('.md', '.txt', '.pdf'))]
        new_chunks = []

        for filename in files:
            filepath = os.path.join(self.kb_dir, filename)
            try:
                text = self._extract_text(filepath)
                if text.strip():
                    doc_chunks = self._chunk_text(filename, text)
                    new_chunks.extend(doc_chunks)
            except Exception as e:
                logger.warning("Failed to ingest file %s: %s", filename, str(e))

        self.chunks = new_chunks
        self._build_index()
        return len(files), len(self.chunks)

    def _extract_text(self, filepath: str) -> str:
        if filepath.endswith('.pdf'):
            try:
                from pypdf import PdfReader
                reader = PdfReader(filepath)
                return "\n".join([page.extract_text() or "" for page in reader.pages])
            except Exception:
                # Fallback if pypdf is not available or file is empty
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
        else:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

    def _chunk_text(self, doc_name: str, text: str, chunk_size: int = 500, overlap: int = 100) -> List[DocumentChunk]:
        """Splits text into sliding-window paragraph chunks."""
        paragraphs = text.split("\n\n")
        chunks = []
        current_text = ""
        chunk_id = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_text) + len(para) <= chunk_size:
                current_text = f"{current_text}\n\n{para}".strip()
            else:
                if current_text:
                    chunks.append(DocumentChunk(doc_name, current_text, chunk_id))
                    chunk_id += 1
                current_text = para

        if current_text:
            chunks.append(DocumentChunk(doc_name, current_text, chunk_id))

        return chunks

    def _build_index(self):
        """Builds BM25 term frequency index over loaded chunks."""
        self.total_docs = len(self.chunks)
        self.doc_freqs = Counter()
        total_len = 0

        for chunk in self.chunks:
            unique_terms = set(chunk.tokens)
            for t in unique_terms:
                self.doc_freqs[t] += 1
            total_len += len(chunk.tokens)

        self.avg_doc_len = (total_len / self.total_docs) if self.total_docs > 0 else 1.0

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[DocumentChunk, float]]:
        """Retrieves most relevant document chunks based on BM25 similarity."""
        if not self.chunks:
            return []

        query_tokens = re.findall(r'\w+', query.lower())
        if not query_tokens:
            return []

        k1 = 1.5
        b = 0.75
        scores = []

        for chunk in self.chunks:
            score = 0.0
            chunk_len = len(chunk.tokens)
            chunk_counts = Counter(chunk.tokens)

            for token in query_tokens:
                if token not in chunk_counts:
                    continue
                df = self.doc_freqs.get(token, 0)
                # BM25 IDF
                idf = math.log(1 + (self.total_docs - df + 0.5) / (df + 0.5))
                # Term Frequency
                tf = chunk_counts[token]
                term_score = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (chunk_len / self.avg_doc_len)))
                score += term_score

            if score > 0:
                scores.append((chunk, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def check_guardrails(self, query: str) -> Optional[str]:
        """Validates query against strict safety and clinical guardrails."""
        q_lower = query.lower()

        # 1. Emergency detection
        for trigger in EMERGENCY_TRIGGERS:
            if trigger in q_lower:
                return (
                    "⚠️ **EMERGENCY MEDICAL WARNING**\n\n"
                    "You described symptoms that may indicate a medical emergency. "
                    "Please call **911** (or your local emergency services such as **112**) or go to the nearest emergency room immediately."
                    f"{DISCLAIMER}"
                )

        # 2. Direct diagnosis refusal
        for trigger in DIAGNOSIS_TRIGGERS:
            if trigger in q_lower:
                return (
                    "I cannot diagnose medical conditions or illnesses. "
                    "Only a licensed healthcare professional can provide a diagnostic evaluation based on your clinical history and diagnostic tests."
                    f"{DISCLAIMER}"
                )

        # 3. Dosage change refusal
        for trigger in DOSAGE_CHANGE_TRIGGERS:
            if trigger in q_lower:
                return (
                    "Never adjust, double, or stop your medication dosage without explicit instructions from your prescribing doctor. "
                    "Altering your regimen can cause serious adverse effects or reduce the therapeutic benefit of your treatment."
                    f"{DISCLAIMER}"
                )

        return None

    def detect_side_effects(self, query: str, user_medicines: List[Dict[str, Any]]) -> Optional[SuggestedFeedback]:
        """
        Cross-references user's query against active medications to identify potential side effects
        and construct a 1-click feedback report hook.
        """
        q_lower = query.lower()
        side_effect_keywords = [
            ("nausea", "Nausea / Stomach Upset", 2),
            ("vomiting", "Nausea / Vomiting", 2),
            ("headache", "Headache", 1),
            ("dizziness", "Dizziness / Lightheadedness", 2),
            ("cough", "Persistent Dry Cough", 2),
            ("swelling", "Peripheral Edema (Swelling)", 3),
            ("rash", "Skin Rash / Itching", 2),
            ("fatigue", "Excessive Fatigue", 2),
            ("muscle pain", "Muscle Pain / Myalgia", 3),
            ("cramps", "Stomach Cramps", 2),
            ("diarrhea", "Diarrhea", 2),
        ]

        matched_effect = None
        matched_severity = 2
        for kw, desc, sev in side_effect_keywords:
            if kw in q_lower:
                matched_effect = desc
                matched_severity = sev
                break

        if not matched_effect:
            return None

        # Check if query mentions a specific medicine or match active medicines
        for med in user_medicines:
            med_name = (med.get("name") or "").lower()
            if med_name and (med_name in q_lower or len(user_medicines) == 1):
                return SuggestedFeedback(
                    medicine_id=med.get("id"),
                    medicine_name=med.get("name", "Current Medication"),
                    possible_side_effect=matched_effect,
                    severity=matched_severity,
                )

        # If user has medicines, associate with first active medicine
        if user_medicines:
            primary_med = user_medicines[0]
            return SuggestedFeedback(
                medicine_id=primary_med.get("id"),
                medicine_name=primary_med.get("name", "Active Medication"),
                possible_side_effect=matched_effect,
                severity=matched_severity,
            )

        return None

    def generate_answer(self, query: str, context_chunks: List[Tuple[DocumentChunk, float]]) -> Tuple[str, List[SourceCitation]]:
        """
        Synthesizes a clean, document-grounded response using retrieved context chunks.
        """
        if not context_chunks:
            answer = (
                "I could not find specific clinical guidance in the Adhera medical reference base matching your exact query. "
                "For your safety, please reach out to your prescribing doctor or pharmacist for guidance."
                f"{DISCLAIMER}"
            )
            return answer, []

        citations = []
        context_snippets = []
        for chunk, score in context_chunks:
            # Clean snippet for display
            clean_snippet = chunk.text.replace("\n", " ")[:200] + "..."
            citations.append(SourceCitation(
                document_name=chunk.doc_name.replace(".md", "").replace("_", " ").title(),
                snippet=clean_snippet,
                score=round(float(score), 2)
            ))
            context_snippets.append(chunk.text)

        # High-quality synthesis based on retrieved medical context
        top_chunk = context_chunks[0][0].text

        # Extract most relevant paragraphs from top chunks
        relevant_lines = []
        for line in top_chunk.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                relevant_lines.append(line)

        summary_body = "\n".join(relevant_lines[:6]) if relevant_lines else top_chunk[:400]

        answer = (
            f"Based on Adhera's clinical reference guidelines:\n\n"
            f"{summary_body}\n\n"
            f"Please remember to log any symptoms in your daily Adhera tracker."
            f"{DISCLAIMER}"
        )

        return answer, citations

    def process_query(self, query: str, user_medicines: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, List[SourceCitation], Optional[SuggestedFeedback]]:
        """Main entry point for medical chat queries."""
        # 1. Guardrail validation
        refusal = self.check_guardrails(query)
        if refusal:
            return refusal, [], None

        # 2. Semantic Document Retrieval
        top_chunks = self.retrieve(query, top_k=3)

        # 3. Grounded Answer Synthesis
        answer, citations = self.generate_answer(query, top_chunks)

        # 4. Side-effect correlation
        suggested_feedback = self.detect_side_effects(query, user_medicines or [])

        return answer, citations, suggested_feedback


# Singleton instance
rag_engine = MedicalRAGEngine()
