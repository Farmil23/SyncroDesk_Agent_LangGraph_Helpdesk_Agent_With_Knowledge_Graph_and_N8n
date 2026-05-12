from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.nodes import (
    triage_node,
    normalize_query_node,
    semantic_cache_lookup_node,
    retriever_node,
    cache_write_node,
    drafter_node,
    guardrail_node,
)

workflow = StateGraph(AgentState)

# Daftar node
workflow.add_node("triage", triage_node)
workflow.add_node("normalize", normalize_query_node)
workflow.add_node("cache_lookup", semantic_cache_lookup_node)
workflow.add_node("investigator", retriever_node)
workflow.add_node("cache_write", cache_write_node)
workflow.add_node("drafter", drafter_node)
workflow.add_node("guardrail", guardrail_node)
workflow.set_entry_point("triage")
workflow.add_edge("triage", "normalize")
workflow.add_edge("normalize", "cache_lookup")


def route_after_cache(state: AgentState):
    """
    Cabang setelah cache_lookup.

    - "hit"  : cache_hit True → retrieved_docs & user_context sudah terisi dari QA_CACHE.
    - "miss" : perlu jalan investigator (Chroma + Neo4j), lalu cache_write, baru drafter.
    """
    return "hit" if state.get("cache_hit") else "miss"


workflow.add_conditional_edges(
    "cache_lookup",
    route_after_cache,
    {
        "hit": "drafter",
        "miss": "investigator",
    },
)

workflow.add_edge("investigator", "cache_write")
workflow.add_edge("cache_write", "drafter")
workflow.add_edge("drafter", "guardrail")


# def check_safety(state):
#     """Kalau draf dianggap aman → selesai; kalau tidak → minta drafter tulis ulang."""
#     return "final" if state["is_safe"] else "re-draft"


# workflow.add_conditional_edges(
#     "guardrail",
#     check_safety,
#     {
#         "final": END,
#         "re-draft": "drafter",
#     },
# )

workflow.add_edge("guardrail", END)

app_graph = workflow.compile()
