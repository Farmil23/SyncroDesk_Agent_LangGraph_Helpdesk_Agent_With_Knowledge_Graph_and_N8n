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

   
    category: str          # IT, HR, atau Finance — dari node triage
    retrieved_docs: str    # Cuplikan SOP dari Chroma
    user_context: str      # Konteks aset/user (Neo4j / placeholder)

    # Output final
    draft_response: str    # Email draf dari node drafter
    is_safe: bool          # True/False dari node guardrail

  
    normalized_issue: NotRequired[str] 
    cache_hit: NotRequired[bool]          
