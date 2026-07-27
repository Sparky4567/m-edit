# memory.py

import json
import os
from datetime import datetime

MEMORY_FILE = "memory.json"


def load_memories():

    if not os.path.exists(MEMORY_FILE):
        return []

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("memories", [])

    except Exception:
        return []


def save_memories(memories):

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"memories": memories},
            f,
            indent=2,
            ensure_ascii=False
        )


def remember(text):

    memories = load_memories()

    memories.append({
        "timestamp": datetime.now().isoformat(),
        "text": text
    })

    save_memories(memories)


def delete_memory(timestamp):

    memories = load_memories()
    remaining_memories = [
        memory
        for memory in memories
        if memory.get("timestamp") != timestamp
    ]

    if len(remaining_memories) == len(memories):
        return False

    save_memories(remaining_memories)
    return True


def update_memory(timestamp, text):

    memories = load_memories()

    for memory in memories:
        if memory.get("timestamp") == timestamp:
            memory["text"] = text
            save_memories(memories)
            return True

    return False


def retrieve_memories(query, limit=10):

    memories = load_memories()

    query_words = set(
        query.lower().split()
    )

    scored = []

    for memory in memories:

        memory_words = set(
            memory["text"].lower().split()
        )

        score = len(
            query_words.intersection(
                memory_words
            )
        )

        if score > 0:
            scored.append(
                (score, memory)
            )

    scored.sort(
        reverse=True,
        key=lambda x: x[0]
    )

    return [
        item[1]["text"]
        for item in scored[:limit]
    ]
