"""
RAG (Retrieval-Augmented Generation) Service with Gemini LLM.

Combines:
1. Vector search over telecom knowledge + project docs
2. Prediction context from ML model
3. Gemini LLM (Google) for analysis

Provides intelligent assistance for network coverage analysis.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import pandas as pd

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

import google.generativeai as genai

from .config import settings

logger = logging.getLogger(__name__)


def _normalize_model_name(model_name: Optional[str]) -> Optional[str]:
    if not model_name:
        return model_name
    return model_name if model_name.startswith("models/") else f"models/{model_name}"


class RAGService:
    """RAG service with prediction-aware analysis."""

    def __init__(self):
        self.chroma_client: Optional[chromadb.Client] = None
        self.collection: Optional[chromadb.Collection] = None
        self.embedder: Optional[SentenceTransformer] = None
        self.llm_model_name: Optional[str] = None
        self.is_initialized: bool = False

    def initialize(self, force_rebuild: bool = False) -> bool:
        """
        Initialize RAG system:
        - Load embedding model
        - Connect to ChromaDB
        - Load or create collection
        - Initialize Gemini client
        - Build knowledge base if needed

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directories
            settings.chroma_db_dir.mkdir(parents=True, exist_ok=True)
            settings.knowledge_base_dir.mkdir(parents=True, exist_ok=True)

            # Initialize embedding model
            logger.info("Loading embedding model...")
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

            # Initialize ChromaDB (new client API)
            logger.info("Initializing ChromaDB...")
            self.chroma_client = chromadb.PersistentClient(
                path=str(settings.chroma_db_dir),
                settings=ChromaSettings(anonymized_telemetry=False)
            )

            # Drop existing collection if rebuild requested
            if force_rebuild:
                try:
                    self.chroma_client.delete_collection(name="telecom_knowledge")
                    logger.info("Deleted existing Chroma collection for rebuild.")
                except Exception as exc:
                    logger.warning("Failed to delete existing collection: %s", exc)

            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="telecom_knowledge",
                metadata={"hnsw:space": "cosine"}
            )

            # Initialize Gemini client
            logger.info("Initializing Gemini client...")
            genai.configure(api_key=settings.gemini_api_key)
            self.llm_model_name = _normalize_model_name(settings.gemini_model)

            # Build knowledge base if empty
            if force_rebuild or self.collection.count() == 0:
                if force_rebuild:
                    logger.info("Rebuilding knowledge base...")
                else:
                    logger.info("Knowledge base empty. Building...")
                self._build_knowledge_base()

            self.is_initialized = True
            logger.info(f"RAG system initialized. Documents: {self.collection.count()}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize RAG: {e}")
            return False

    def _build_knowledge_base(self):
        """Build vector store from knowledge base documents."""
        documents = []
        metadatas = []
        ids = []

        # 1. Load knowledge base documents
        kb_root = settings.knowledge_base_dir
        if kb_root.exists():
            for file_path in kb_root.rglob("*.md"):
                if not file_path.is_file():
                    continue
                try:
                    content = file_path.read_text(encoding='utf-8')
                    # Split into chunks (simple: by paragraphs)
                    chunks = self._split_text(content, chunk_size=500, overlap=50)
                    for i, chunk in enumerate(chunks):
                        rel_path = file_path.relative_to(kb_root).as_posix()
                        documents.append(chunk)
                        metadatas.append({
                            'source': f'knowledge_base/{rel_path}',
                            'chunk': i,
                            'type': 'telecom_doc'
                        })
                        ids.append(f"{file_path.stem}_{i}")
                except Exception as e:
                    logger.warning(f"Failed to load {file_path}: {e}")

        # 2. Load project-specific documents from output/
        output_dir = settings.output_dir
        if output_dir.exists():
            # Model comparison report
            model_comp = output_dir / "model_comparison.csv"
            if model_comp.exists():
                try:
                    df = pd.read_csv(model_comp)
                    summary = f"Model Comparison:\n{df.to_string()}"
                    documents.append(summary)
                    metadatas.append({
                        'source': 'project/model_comparison.csv',
                        'type': 'model_report'
                    })
                    ids.append("model_comparison")
                except Exception as e:
                    logger.warning(f"Failed to load model comparison: {e}")

            # Cell recommendations
            cell_rec = output_dir / "cell_recommendations.csv"
            if cell_rec.exists():
                try:
                    df = pd.read_csv(cell_rec)
                    summary = f"Cell Recommendations (top 20):\n{df.head(20).to_string()}"
                    documents.append(summary)
                    metadatas.append({
                        'source': 'project/cell_recommendations.csv',
                        'type': 'cell_analysis'
                    })
                    ids.append("cell_recommendations")
                except Exception as e:
                    logger.warning(f"Failed to load cell recommendations: {e}")

        # 3. Extract notebook insights (markdown cells from notebooks)
        # Simple extraction: read notebook JSON and extract markdown cells
        notebooks = [
            "Network_Coverage_ML_Pipeline.ipynb",
            "modele.ipynb"
        ]
        for nb_file in notebooks:
            nb_path = Path(__file__).resolve().parent.parent / nb_file
            if nb_path.exists():
                try:
                    import json
                    nb = json.loads(nb_path.read_text(encoding='utf-8'))
                    md_cells = [
                        cell['source'] for cell in nb.get('cells', [])
                        if cell.get('cell_type') == 'markdown'
                    ]
                    # Take first few markdown cells as domain knowledge
                    for i, md_content in enumerate(md_cells[:5]):
                        text = ' '.join(md_content) if isinstance(md_content, list) else md_content
                        if len(text) > 100:  # Only include substantial content
                            documents.append(text[:1000])
                            metadatas.append({
                                'source': f'notebook/{nb_file}#cell{i}',
                                'type': 'notebook_insight'
                            })
                            ids.append(f"{nb_file}_md{i}")
                except Exception as e:
                    logger.warning(f"Failed to extract from {nb_file}: {e}")

        # Add all documents to ChromaDB
        if documents:
            logger.info(f"Embedding {len(documents)} documents...")
            embeddings = self.embedder.encode(documents, show_progress_bar=False)

            self.collection.add(
                documents=documents,
                embeddings=embeddings.tolist(),
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(documents)} documents to knowledge base")
        else:
            logger.warning("No documents found to add to knowledge base")

    def _split_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = words[i:i + chunk_size]
            chunks.append(' '.join(chunk))
        return chunks

    def retrieve(
        self,
        query: str,
        prediction_context: Optional[Dict[str, Any]] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents from knowledge base.

        Args:
            query: User's question
            prediction_context: Optional prediction results to enrich search
            k: Number of documents to retrieve

        Returns:
            List of {content, source, metadata, score}
        """
        if not self.is_initialized:
            raise RuntimeError("RAG service not initialized. Call initialize() first.")

        # Enrich query with prediction context
        enriched_query = query
        if prediction_context:
            prediction_type = prediction_context.get('prediction_type')
            predicted_class = (
                prediction_context.get('predicted_class')
                or prediction_context.get('class')
                or prediction_context.get('class_label')
            )
            confidence = prediction_context.get('confidence')

            if prediction_type:
                enriched_query = f"{prediction_type} analysis. {enriched_query}"

            if predicted_class:
                if confidence is not None:
                    enriched_query = (
                        f"Coverage class {predicted_class} (confidence: {confidence:.1f}%). {query}"
                    )
                else:
                    enriched_query = f"Coverage class {predicted_class}. {query}"

            probabilities = prediction_context.get('probabilities', {})
            if probabilities:
                top_probs = sorted(
                    probabilities.items(), key=lambda item: item[1], reverse=True
                )[:2]
                prob_text = ', '.join(
                    f"{label}: {float(value) * 100:.1f}%" for label, value in top_probs
                )
                enriched_query += f" Probabilities: {prob_text}"

        # Encode query
        query_embedding = self.embedder.encode([enriched_query])

        # Search
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=min(k, self.collection.count()),
            include=['documents', 'metadatas', 'distances']
        )

        # Format results
        retrieved = []
        if results['documents'] and results['documents'][0]:
            for doc, meta, distance in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                retrieved.append({
                    'content': doc[:500],  # Limit content length
                    'source': meta.get('source', 'Unknown'),
                    'type': meta.get('type', 'unknown'),
                    'score': float(1 - distance)  # Convert cosine distance to similarity
                })

        return retrieved

    def analyze(
        self,
        question: str,
        prediction: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        k_docs: int = 3
    ) -> Dict[str, Any]:
        """
        Analyze question using RAG + LLM.

        Args:
            question: User's question
            prediction: Optional prediction results for context
            model: Gemini model name (default from config)
            k_docs: Number of retrieval results to include

        Returns:
            Dictionary with answer, sources, model_used
        """
        if not self.is_initialized:
            raise RuntimeError("RAG service not initialized.")

        # 1. Retrieve relevant documents
        retrieved = self.retrieve(question, prediction_context=prediction, k=k_docs)

        # 2. Build context
        context_str = "\n\n".join([
            f"Source: {item['source']}\n{item['content']}"
            for item in retrieved
        ])

        # 3. Build system prompt
        system_prompt = """You are a senior network engineer specializing in coverage and QoS analysis.

    Your role is to analyze predictions and provide actionable recommendations based on:
    - Model predictions (class, confidence, class probabilities)
    - Key KPIs (RSRP, RSRQ, throughput, band, PCI, temporal patterns)
    - Relevant telecom knowledge (KPI thresholds, QoS guidance, coverage best practices)
    - Project-specific insights from past analysis

    Always:
    1. Reference specific values from the prediction
    2. Explain the telecom reasoning
    3. Provide step-by-step troubleshooting actions
    4. Cite your sources (doc name or section like "kpi_thresholds.md")
    5. Consider both immediate and long-term solutions

    If the prediction is QoS and the class is "Mauvaise" or "Assez bien":
    - Check RSRP/RSRQ levels and throughput headroom
    - Suggest mitigation (tilt, power, interference checks, capacity relief)

    If the prediction is Coverage and the class is "Mauvaise" or "Moyenne":
    - Check RSRQ and throughput trends
    - Suggest antenna tilt or power adjustments
    - Investigate interference, congestion, or coverage holes

    Be concise, technical, and specific. Avoid generic advice."""

        # 4. Build user message with prediction context
        user_message = ""
        if prediction:
            prediction_type = prediction.get('prediction_type') or 'coverage'
            predicted_class = prediction.get('predicted_class', 'N/A')
            confidence = prediction.get('confidence')
            probabilities = prediction.get('probabilities', {})
            prob_text = ', '.join(
                f"{label}: {float(value) * 100:.2f}%" for label, value in probabilities.items()
            ) if probabilities else 'None'
            confidence_text = f"{confidence:.2f}%" if confidence is not None else 'N/A'

            header = "QoS" if prediction_type == 'qos' else "Coverage"
            user_message += f"""**Current {header} Prediction:**
- Predicted Class: {predicted_class}
- Confidence: {confidence_text}
- Probabilities: {prob_text}

"""
        else:
            user_message += "No specific prediction provided. Answer based on general telecom knowledge.\n\n"

        user_message += f"""**User Question:** {question}

**Relevant Documentation:**
{context_str if context_str else '[No relevant documents found in knowledge base]'}

Please provide a detailed analysis and specific recommendations.
"""

        # 5. Call LLM
        try:
            model_to_use = _normalize_model_name(model or settings.gemini_model)
            model_client = genai.GenerativeModel(
                model_name=model_to_use,
                system_instruction=system_prompt
            )

            response = model_client.generate_content(
                user_message,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 1500
                }
            )

            answer = getattr(response, "text", None) or ""
            if not answer and getattr(response, "candidates", None):
                parts = response.candidates[0].content.parts if response.candidates[0].content else []
                answer = "".join([getattr(part, "text", "") for part in parts]).strip()

            if not answer:
                raise RuntimeError("Empty response from Gemini")

            usage = getattr(response, "usage_metadata", None)
            if isinstance(usage, dict):
                prompt_tokens = usage.get("prompt_token_count")
                completion_tokens = usage.get("candidates_token_count")
            else:
                prompt_tokens = getattr(usage, "prompt_token_count", None) if usage else None
                completion_tokens = getattr(usage, "candidates_token_count", None) if usage else None

            return {
                'answer': answer,
                'model_used': model_to_use,
                'sources': [item['source'] for item in retrieved],
                'tokens_used': {
                    'prompt': prompt_tokens,
                    'completion': completion_tokens
                }
            }

        except Exception as e:
            logger.error(f"LLM API error: {e}")
            return {
                'answer': f"Error: Failed to get response from LLM. {str(e)}",
                'model_used': model or settings.gemini_model,
                'sources': [],
                'error': True
            }

    def get_status(self) -> Dict[str, Any]:
        """Get RAG system status."""
        return {
            'initialized': self.is_initialized,
            'document_count': self.collection.count() if self.collection else 0,
            'embedding_model': 'all-MiniLM-L6-v2' if self.embedder else None,
            'llm_model': self.llm_model_name if self.llm_model_name else None
        }


# Global RAG service instance
rag_service = RAGService()
