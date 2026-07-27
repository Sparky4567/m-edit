import os
import json
from pathlib import Path

APP_SETTINGS_FILE = Path("app_settings.json")

def list_workspaces():
    try:
        if APP_SETTINGS_FILE.exists():
            settings = json.loads(APP_SETTINGS_FILE.read_text(encoding="utf-8"))
            if "workspaces" in settings and isinstance(settings["workspaces"], list):
                return settings["workspaces"]
    except Exception:
        pass
    return [{"id": "default", "name": "Current Workspace"}]

def get_working_directory():
    try:
        if APP_SETTINGS_FILE.exists():
            settings = json.loads(APP_SETTINGS_FILE.read_text(encoding="utf-8"))
            saved_dir = settings.get("working_directory")
            if saved_dir and Path(saved_dir).is_dir():
                return Path(saved_dir)
    except Exception:
        pass
    return Path.cwd()

def retrieve_workspace_chunks(query, workspace_id=None, limit=5):
    work_dir = get_working_directory()
    query_words = set(query.lower().split())
    if not query_words:
        return []

    chunks = []
    try:
        for root, dirs, files in os.walk(work_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["venv", ".venv", "node_modules", "target", "build", "dist"]]
            for file in files:
                if file.endswith(".md"):
                    file_path = Path(root) / file
                    try:
                        text = file_path.read_text(errors="ignore")
                        lines = text.splitlines()
                        current_chunk = []
                        chunk_idx = 0
                        for line in lines:
                            if line.strip() == "":
                                if current_chunk:
                                    chunk_text = "\n".join(current_chunk)
                                    words = set(chunk_text.lower().split())
                                    score = len(query_words.intersection(words))
                                    if score > 0:
                                        try:
                                            rel_path = str(file_path.relative_to(work_dir))
                                        except ValueError:
                                            rel_path = file_path.name
                                        chunks.append({
                                            "workspace_name": "Workspace",
                                            "filename": rel_path,
                                            "page": 1,
                                            "chunk_index": chunk_idx,
                                            "text": chunk_text,
                                            "score": score
                                        })
                                    current_chunk = []
                                    chunk_idx += 1
                            else:
                                current_chunk.append(line)
                        if current_chunk:
                            chunk_text = "\n".join(current_chunk)
                            words = set(chunk_text.lower().split())
                            score = len(query_words.intersection(words))
                            if score > 0:
                                try:
                                    rel_path = str(file_path.relative_to(work_dir))
                                except ValueError:
                                    rel_path = file_path.name
                                chunks.append({
                                    "workspace_name": "Workspace",
                                    "filename": rel_path,
                                    "page": 1,
                                    "chunk_index": chunk_idx,
                                    "text": chunk_text,
                                    "score": score
                                })
                    except Exception:
                        pass
    except Exception:
        pass

    chunks.sort(key=lambda x: x["score"], reverse=True)
    return chunks[:limit]

def write_about_prompt(topic, workspace_id=None):
    chunks = retrieve_workspace_chunks(topic, workspace_id=workspace_id, limit=5)
    if not chunks:
        work_dir = get_working_directory()
        collected = []
        try:
            for root, dirs, files in os.walk(work_dir):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["venv", ".venv", "node_modules", "target", "build", "dist"]]
                for file in files:
                    if file.endswith(".md"):
                        p = Path(root) / file
                        try:
                            content = p.read_text(errors="ignore")
                            if content.strip():
                                collected.append(f"--- Note ({p.name}) ---\n{content}")
                        except Exception:
                            pass
        except Exception:
            pass

        if collected:
            context = "\n\n".join(collected[:5])
            prompt = f"User asked for notes about: {topic}\n\nHere are the available workspace notes:\n{context}\n\nPlease interpret and summarize the notes accurately regarding '{topic}'."
            return prompt, chunks
        return None, None

    context = "\n\n".join([f"[{item['filename']}]\n{item['text']}" for item in chunks])
    prompt = f"User asked for information about: {topic}\n\nRelevant excerpts from notes:\n{context}\n\nPlease interpret the above notes and answer the user's question about '{topic}' thoroughly and accurately."
    return prompt, chunks
