"""
memory_service.py — Persistent AI memory via Mem0.

If MEM0_API_KEY is set, uses the hosted Mem0 platform.
If absent, falls back to local in-memory mode (data is lost on restart).

Public API:
  add_memory(user_id, content, metadata=None)
  get_relevant_memories(user_id, query, limit=5) -> list[str]
"""
import os
from dotenv import load_dotenv

load_dotenv()

_mem0_client = None


def _get_client():
    """Lazy-initialise the Mem0 client (once per process)."""
    global _mem0_client
    if _mem0_client is not None:
        return _mem0_client

    api_key = os.getenv("MEM0_API_KEY", "").strip()

    try:
        if api_key:
            # Hosted Mem0 platform
            from mem0 import MemoryClient
            _mem0_client = MemoryClient(api_key=api_key)
            print("[Mem0] Using hosted platform (MemoryClient)")
        else:
            # Local in-process memory (no external dependency needed beyond mem0ai)
            from mem0 import Memory
            _mem0_client = Memory()
            print("[Mem0] Using local in-memory mode (no MEM0_API_KEY set)")
    except Exception as e:
        print(f"[Mem0] Initialisation warning: {e} — memory features disabled")
        _mem0_client = None

    return _mem0_client


def add_memory(user_id: str, content: str, metadata: dict = None) -> None:
    """
    Store a memory entry tied to a user.

    Silently skips if:
    - user_id is None / empty
    - Mem0 client failed to initialise
    """
    if not user_id:
        return

    client = _get_client()
    if client is None:
        return

    try:
        messages = [{"role": "user", "content": content}]
        kwargs = {"user_id": user_id, "messages": messages}
        if metadata:
            kwargs["metadata"] = metadata
        client.add(**kwargs)
    except Exception as e:
        # Memory is best-effort — don't crash the request
        print(f"[Mem0] add_memory error (non-fatal): {e}")


def get_relevant_memories(user_id: str, query: str, limit: int = 5) -> list[str]:
    """
    Retrieve memories relevant to the current query for a given user.

    Returns an empty list if:
    - user_id is None / empty
    - Mem0 client failed to initialise
    - Search raises an exception
    """
    if not user_id:
        return []

    client = _get_client()
    if client is None:
        return []

    try:
        results = client.search(query=query, user_id=user_id, limit=limit)
        # Mem0 returns a list of dicts with a "memory" key
        if isinstance(results, list):
            memories = []
            for r in results:
                if isinstance(r, dict):
                    mem_text = r.get("memory") or r.get("text") or str(r)
                else:
                    mem_text = str(r)
                if mem_text:
                    memories.append(mem_text)
            return memories
        return []
    except Exception as e:
        print(f"[Mem0] get_relevant_memories error (non-fatal): {e}")
        return []
