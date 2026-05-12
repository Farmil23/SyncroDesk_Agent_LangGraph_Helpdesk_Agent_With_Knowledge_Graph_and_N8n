from typing import Annotated, List, TypedDict
from typing_extensions import NotRequired
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    # Pesan percakapan (riwayat)
    messages: Annotated[List[BaseMessage], operator.add]

    # Data mentah dari n8n
    ticket_id: str
    issue_text: str
    user_email: str

    # Data hasil investigasi
    category: str          # IT, HR, atau Finance — dari node triage
    retrieved_docs: str    # Cuplikan SOP dari Chroma (atau dari cache FAISS)
    user_context: str      # Konteks aset/user (Neo4j / placeholder)

    # Output final
    draft_response: str    # Email draf dari node drafter
    is_safe: bool          # True/False dari node guardrail

    # --- Field khusus cache FAISS (opsional di awal invoke; bisa diisi node) ---
    # NotRequired = field ini boleh belum ada saat pertama kali state dibuat;
    # nanti node "normalize" / "cache_lookup" yang mengisinya.
    normalized_issue: NotRequired[str]  # Satu string rapat untuk pencarian vector cache
    cache_hit: NotRequired[bool]          # True jika konteks diambil dari QA_CACHE, bukan dari DB
