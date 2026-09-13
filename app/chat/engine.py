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
                import importlib
                pypdf = importlib.import_module("pypdf")
                reader = pypdf.PdfReader(filepath)
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

    def _build_patient_context(self, patient_context: Optional[Dict[str, Any]], user_medicines: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Normalizes patient context from router and user_medicines."""
        ctx = patient_context or {}
        meds = ctx.get("medicines") or user_medicines or []
        profile = ctx.get("profile") or {}
        feedback = ctx.get("recent_feedback") or []
        adherence = ctx.get("adherence_summary") or {}
        return {
            "medicines": meds,
            "profile": profile,
            "recent_feedback": feedback,
            "adherence_summary": adherence,
        }

    def _call_gemini(self, query: str, patient_summary: str, context_text: str) -> Optional[str]:
        """Optional Gemini LLM call path if API key is present in environment."""
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return None

        try:
            import httpx
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            system_instruction = (
                "You are the ADHERA Medical Knowledge Assistant. Provide personalized, clinical, compassionate answers. "
                "CRITICAL RULES:\n"
                "1. ONLY discuss conditions and medications relevant to the patient's active regimen or explicitly asked in the query.\n"
                "2. NEVER assume the patient has diabetes, hypertension, or any condition unless present in their regimen or query.\n"
                "3. Reference their actual medicines, dosages, and adherence history where helpful.\n"
                "4. Keep explanations concise, clear, and practical.\n"
                "5. Never give direct diagnostic declarations or recommend dosage alterations."
            )
            prompt = (
                f"### Patient Context:\n{patient_summary}\n\n"
                f"### Clinical Knowledge Chunks:\n{context_text}\n\n"
                f"### Patient Question:\n{query}"
            )
            payload = {
                "system_instruction": {"parts": [{"text": system_instruction}]},
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600}
            }
            res = httpx.post(url, json=payload, timeout=3.5)
            if res.status_code == 200:
                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text.strip()
        except Exception as e:
            logger.info("Gemini call skipped/failed, using deterministic synthesis: %s", str(e))
        return None

    def _synthesize_personalized_answer(
        self,
        query: str,
        context_chunks: List[Tuple[DocumentChunk, float]],
        patient_ctx: Dict[str, Any]
    ) -> str:
        """
        Deterministic, highly personalized RAG synthesis tailored to the patient's actual regimen,
        adherence pattern, and logged symptoms.
        """
        medicines = patient_ctx.get("medicines") or []
        feedback = patient_ctx.get("recent_feedback") or []
        adherence = patient_ctx.get("adherence_summary") or {}
        q_lower = query.lower()

        sections = []

        # 1. Regimen Context Header
        if medicines:
            med_lines = []
            for m in medicines:
                name = m.get("name", "Prescription")
                amt = m.get("dosage_amount")
                unit = m.get("dosage_unit") or ""
                freq = m.get("frequency_type") or m.get("frequency") or "daily"
                dose_str = f" {amt} {unit}".strip() if amt else ""
                inst = f" ({m['instructions']})" if m.get("instructions") else ""
                med_lines.append(f"• **{name}**{dose_str} — {freq.capitalize()}{inst}")

            sections.append(
                "**Your Current Regimen:**\n" + "\n".join(med_lines)
            )
        else:
            sections.append(
                "**Your Current Regimen:**\n• No active medications currently recorded in your Adhera profile."
            )

        # 2. Personalized Guidance tailored to their specific medications
        guidance_points = []
        user_med_names = [m.get("name", "").lower() for m in medicines if m.get("name")]

        # Match specific guidance for patient's medicines from knowledge base
        for chunk, _ in context_chunks:
            chunk_text = chunk.text
            # Parse sub-sections in the chunk
            subsections = re.split(r'\n(?=###?\s+)', chunk_text)
            for sub in subsections:
                sub_clean = sub.strip()
                if not sub_clean:
                    continue
                sub_lower = sub_clean.lower()

                # Determine relevance:
                # A) Matches one of patient's active medicines
                # B) Is general adherence/timing/missed dose/wellness guidance
                # C) User explicitly mentioned the topic in their query
                is_user_med = any(m_name in sub_lower for m_name in user_med_names)
                is_general_adherence = any(k in sub_lower for k in [
                    "missed dose", "consistency", "pairing with habits", "safe medication storage",
                    "mental wellness", "daily routine & timing", "food requirements", "severity grading"
                ])
                is_explicitly_queried = any(word in sub_lower for word in q_lower.split() if len(word) > 4)

                # Exclude drug/condition-specific chunks for drugs the patient is NOT taking unless explicitly queried
                is_other_drug = any(other in sub_lower for other in ["metformin", "lisinopril", "amlodipine", "atorvastatin", "levothyroxine", "omeprazole", "losartan"])
                if is_other_drug and not is_user_med and not is_explicitly_queried:
                    continue

                if is_user_med or is_general_adherence or is_explicitly_queried:
                    # Clean markdown headers for inline bullet readability
                    cleaned_lines = [line.strip() for line in sub_clean.split("\n") if line.strip()]
                    cleaned_body = "\n".join(cleaned_lines[:5])
                    if cleaned_body not in guidance_points:
                        guidance_points.append(cleaned_body)

        if guidance_points:
            sections.append("### Clinical Guidance & Instructions:\n" + "\n\n".join(guidance_points[:3]))
        else:
            # Fallback general safety & adherence guidance
            sections.append(
                "### Clinical Guidance & Instructions:\n"
                "• **Consistency**: Take your daily doses at the same scheduled time each day.\n"
                "• **Missed Doses**: If you miss a dose, take it as soon as you remember. If it is close to your next scheduled dose, skip the missed dose. Never take a double dose.\n"
                "• **Storage**: Store medications in a cool, dry place away from heat and direct moisture."
            )

        # 3. Adherence & Symptom Contextual Notes
        notes = []
        if adherence and adherence.get("missed_doses_7d", 0) > 0:
            missed = adherence["missed_doses_7d"]
            rate = adherence.get("weekly_rate")
            rate_str = f" (weekly rate: {rate}%)" if rate is not None else ""
            notes.append(
                f"📊 **Adherence Note**: You have **{missed} missed dose{'s' if missed != 1 else ''}** recorded in the last 7 days{rate_str}. Pairing doses with daily anchors (like breakfast or brushing teeth) helps build steady habits."
            )

        if feedback:
            latest_fb = feedback[0]
            desc = latest_fb.get("description")
            if desc:
                notes.append(
                    f"⚠️ **Recent Symptom Note**: You previously reported: *\"{desc}\"*. Please consult your healthcare provider if these symptoms persist or worsen."
                )

        if notes:
            sections.append("\n\n".join(notes))

        return "\n\n".join(sections)

    def generate_answer(
        self,
        query: str,
        context_chunks: List[Tuple[DocumentChunk, float]],
        patient_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[SourceCitation]]:
        """
        Synthesizes a document-grounded response personalized to the patient's regimen.
        """
        ctx = self._build_patient_context(patient_context)
        citations = []
        context_texts = []

        for chunk, score in context_chunks:
            clean_snippet = chunk.text.replace("\n", " ")[:200] + "..."
            citations.append(SourceCitation(
                document_name=chunk.doc_name.replace(".md", "").replace("_", " ").title(),
                snippet=clean_snippet,
                score=round(float(score), 2)
            ))
            context_texts.append(chunk.text)

        # 1. Try Gemini generation if API key is present
        gemini_response = self._call_gemini(
            query=query,
            patient_summary=str(ctx),
            context_text="\n\n---\n\n".join(context_texts[:3])
        )

        if gemini_response:
            answer = f"{gemini_response}{DISCLAIMER}"
            return answer, citations

        # 2. Deterministic Personalized Synthesis
        personalized_body = self._synthesize_personalized_answer(query, context_chunks, ctx)
        answer = f"{personalized_body}{DISCLAIMER}"
        return answer, citations

    def process_query(
        self,
        query: str,
        user_medicines: Optional[List[Dict[str, Any]]] = None,
        patient_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[SourceCitation], Optional[SuggestedFeedback]]:
        """Main entry point for medical chat queries."""
        # 1. Guardrail validation
        refusal = self.check_guardrails(query)
        if refusal:
            return refusal, [], None

        # 2. Build full patient context
        norm_ctx = self._build_patient_context(patient_context, user_medicines)
        active_meds = norm_ctx["medicines"]

        # 3. Semantic Document Retrieval (augment query with active medicine names for better recall)
        med_keywords = " ".join([m.get("name", "") for m in active_meds if m.get("name")])
        retrieval_query = f"{query} {med_keywords}".strip()
        top_chunks = self.retrieve(retrieval_query, top_k=4)

        # Fallback to pure query retrieval if combined query yields no results
        if not top_chunks:
            top_chunks = self.retrieve(query, top_k=3)

        # 4. Grounded, Personalized Answer Synthesis
        answer, citations = self.generate_answer(query, top_chunks, norm_ctx)

        # 5. Side-effect correlation
        suggested_feedback = self.detect_side_effects(query, active_meds)

        return answer, citations, suggested_feedback


# Singleton instance
rag_engine = MedicalRAGEngine()
