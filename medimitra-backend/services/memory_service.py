"""
memory_service.py — Persistent AI memory via Mem0.

If MEM0_API_KEY is set, uses the hosted Mem0 platform.
If absent, falls back to local in-memory mode (data is lost on restart).

Public API:
  add_memory(user_id, content, metadata=None)
  get_relevant_memories(user_id, query, limit=5) -> list[str]
  store_profile_memory(user_id, profile)
  get_user_health_context(user_id) -> str
"""
import os
import json
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


def get_user_health_context(user_id) -> str:
    """
    Returns a formatted string of the user's health data for injection into AI prompts.

    Strategy:
    1. First tries SQLite (faster, always available, most up-to-date)
    2. Returns empty string gracefully if no profile or any error occurs
    3. Mem0 is supplementary — DB is the source of truth for profile context

    Args:
        user_id: Can be int or str — handles both.

    Returns:
        Formatted health context string, or "" if no profile found.
    """
    if not user_id:
        return ""

    # Safely convert to int — if it fails (e.g. empty string), return ""
    try:
        uid_int = int(user_id)
    except (ValueError, TypeError):
        print(f"[get_user_health_context] Invalid user_id: {user_id!r}")
        return ""

    if uid_int <= 0:
        return ""

    try:
        from database import get_connection
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT full_name, age, gender, blood_group, height_cm, weight_kg, "
                "allergies, chronic_conditions, current_medications, past_surgeries, "
                "emergency_contact_name, emergency_contact_phone, emergency_contact_relation "
                "FROM health_profiles WHERE user_id = ?",
                (uid_int,)
            ).fetchone()
        finally:
            conn.close()

        if not row:
            print(f"[get_user_health_context] No profile found for user_id={uid_int}")
            return ""

        allergies   = json.loads(row["allergies"])           if row["allergies"]           else []
        conditions  = json.loads(row["chronic_conditions"])  if row["chronic_conditions"]  else []
        meds        = json.loads(row["current_medications"]) if row["current_medications"] else []
        surgeries   = json.loads(row["past_surgeries"])      if row["past_surgeries"]      else []

        lines = []
        if row["full_name"]:   lines.append(f"Name: {row['full_name']}")
        if row["age"]:         lines.append(f"Age: {row['age']}")
        if row["gender"]:      lines.append(f"Gender: {row['gender']}")
        if row["blood_group"]: lines.append(f"Blood Group: {row['blood_group']}")

        if row["height_cm"] and row["weight_kg"]:
            try:
                bmi = round(row["weight_kg"] / ((row["height_cm"] / 100) ** 2), 1)
                lines.append(f"Height: {row['height_cm']} cm, Weight: {row['weight_kg']} kg, BMI: {bmi}")
            except Exception:
                lines.append(f"Height: {row['height_cm']} cm, Weight: {row['weight_kg']} kg")
        elif row["height_cm"]:
            lines.append(f"Height: {row['height_cm']} cm")
        elif row["weight_kg"]:
            lines.append(f"Weight: {row['weight_kg']} kg")

        lines.append(f"Allergies: {', '.join(allergies) if allergies else 'None known'}")
        lines.append(f"Chronic Conditions: {', '.join(conditions) if conditions else 'None'}")
        lines.append(f"Current Medications: {', '.join(meds) if meds else 'None'}")

        if surgeries:
            lines.append(f"Past Surgeries: {', '.join(surgeries)}")

        ec_parts = []
        if row["emergency_contact_name"]:     ec_parts.append(row["emergency_contact_name"])
        if row["emergency_contact_relation"]: ec_parts.append(f"({row['emergency_contact_relation']})")
        if row["emergency_contact_phone"]:    ec_parts.append(row["emergency_contact_phone"])
        if ec_parts:
            lines.append(f"Emergency Contact: {' '.join(ec_parts)}")

        context = "\n".join(lines)
        print(f"[get_user_health_context] Loaded profile for user_id={uid_int}: {len(lines)} fields")
        return context

    except Exception as e:
        print(f"[get_user_health_context] Error (non-fatal): {e}")
        return ""


def store_profile_memory(user_id: str, profile: dict) -> None:
    """
    Persist the user's health profile as a structured Mem0 memory so that
    every AI route (symptom, lifestyle, advisor …) can retrieve it.

    On profile save (PUT /api/profile/me), automatically store complete
    health context in Mem0 for AI personalisation.
    """
    if not user_id:
        return

    full_name    = profile.get("full_name", "")
    age          = profile.get("age", "")
    gender       = profile.get("gender", "")
    blood_group  = profile.get("blood_group", "")
    height_cm    = profile.get("height_cm", "")
    weight_kg    = profile.get("weight_kg", "")
    allergies    = profile.get("allergies") or []
    conditions   = profile.get("chronic_conditions") or []
    meds         = profile.get("current_medications") or []
    surgeries    = profile.get("past_surgeries") or []
    ec_name      = profile.get("emergency_contact_name", "")
    ec_relation  = profile.get("emergency_contact_relation", "")
    ec_phone     = profile.get("emergency_contact_phone", "")

    # Compute BMI if possible
    bmi_str = ""
    if height_cm and weight_kg:
        try:
            bmi = round(float(weight_kg) / ((float(height_cm) / 100) ** 2), 1)
            bmi_str = f", BMI: {bmi}"
        except Exception:
            pass

    memory_text = (
        f"Patient Profile for user {user_id}:\n"
        f"Name: {full_name}\n"
        f"Age: {age}, Gender: {gender}\n"
        f"Blood Group: {blood_group}\n"
        f"Height: {height_cm}cm, Weight: {weight_kg}kg{bmi_str}\n"
        f"Allergies: {', '.join(allergies) if allergies else 'None'}\n"
        f"Chronic Conditions: {', '.join(conditions) if conditions else 'None'}\n"
        f"Current Medications: {', '.join(meds) if meds else 'None'}\n"
        f"Past Surgeries: {', '.join(surgeries) if surgeries else 'None'}\n"
        f"Emergency Contact: {ec_name} ({ec_relation}) - {ec_phone}"
    )

    add_memory(user_id=user_id, content=memory_text, metadata={"type": "health_profile"})
