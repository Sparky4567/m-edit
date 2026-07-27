import asyncio
import io
import json
import time
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

import requests

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters
)

from memory import (
    remember,
    retrieve_memories
)
from workspace_docs import retrieve_workspace_chunks, write_about_prompt
from Agentic_Module import Agentic_Module

def ollama_answer_with_model(messages, model_name="llama3"):
    from langchain_ollama import OllamaLLM
    llm = OllamaLLM(model=model_name)
    sys_content = []
    user_content = []
    for m in messages:
        if m.get("role") == "system":
            sys_content.append(m.get("content", ""))
        else:
            user_content.append(m.get("content", ""))

    full_prompt = ""
    if sys_content:
        full_prompt += "System Instructions:\n" + "\n\n".join(sys_content) + "\n\n"
    if user_content:
        full_prompt += "User Request:\n" + "\n\n".join(user_content)

    return llm.invoke(full_prompt)


class TelegramBotRunner:
    def __init__(
        self,
        token: str,
        system_prompt: str = "",
        model_name: str = "llama3",
        working_dir: str = None,
        notify_cb=None,
        proactive_enabled: bool = False,
        proactive_timer: int = 30,
        last_chat_id: int | None = None,
        chat_id_cb=None
    ):
        self.token = token
        self.system_prompt = system_prompt or "You are a helpful assistant."
        self.model_name = model_name or "llama3"
        self.working_dir = working_dir
        self.notify_cb = notify_cb
        self.proactive_enabled = proactive_enabled
        self.proactive_timer = proactive_timer
        self.last_chat_id = last_chat_id
        self.chat_id_cb = chat_id_cb
        self.app = None
        self._running = False
        self._proactive_task = None
        self._last_interaction_time = time.time()

    def update_proactive_settings(self, enabled: bool, timer_minutes: int):
        prev_enabled = self.proactive_enabled
        prev_timer = self.proactive_timer
        self.proactive_enabled = enabled
        self.proactive_timer = max(1, timer_minutes)
        if prev_enabled != enabled or prev_timer != self.proactive_timer:
            self._last_interaction_time = time.time()

    def reset_proactive_timer(self):
        self._last_interaction_time = time.time()

    async def _run_proactive_loop(self):
        while self._running:
            await asyncio.sleep(5)
            if not self._running:
                break
            if not self.proactive_enabled:
                continue

            timer_seconds = max(5, int(self.proactive_timer * 60))
            elapsed = time.time() - self._last_interaction_time
            if elapsed >= timer_seconds:
                self._last_interaction_time = time.time()
                if self.last_chat_id and self.app and self.app.bot:
                    await self.send_proactive_message()

    async def send_proactive_message(self):
        if not self.last_chat_id or not self.app or not self.app.bot:
            return

        memories = retrieve_memories("check-in", limit=3)
        workspace_chunks = retrieve_workspace_chunks("notes", limit=3)

        system_instructions = self.system_prompt
        if memories:
            mem_block = "\n".join([f"- {m}" for m in memories])
            system_instructions += f"\n\nRelevant past memories:\n{mem_block}"
        if workspace_chunks:
            chunk_block = "\n\n".join([f"[{c['filename']}]\n{c['text']}" for c in workspace_chunks])
            system_instructions += f"\n\nRelevant workspace note excerpts:\n{chunk_block}"

        messages = [
            {"role": "system", "content": system_instructions},
            {
                "role": "user",
                "content": (
                    "The proactive conversation timer countdown has reached zero. "
                    "Write a proactive, friendly, and engaging message to start a conversation with the user. "
                    "Offer assistance, share a helpful thought, or check in on their progress or notes. "
                    "Keep it natural and concise."
                )
            }
        ]

        try:
            answer = await asyncio.to_thread(ollama_answer_with_model, messages, self.model_name)
            if answer and answer.strip():
                await self.app.bot.send_message(chat_id=self.last_chat_id, text=answer.strip())
                if self.notify_cb:
                    self.notify_cb("Telegram Bot: Proactive message sent to user.")
        except Exception as err:
            if self.notify_cb:
                self.notify_cb(f"Telegram Bot proactive message error: {err}")

    async def start(self):
        if not self.token:
            if self.notify_cb:
                self.notify_cb("No Telegram token provided.")
            return False

        try:
            builder = ApplicationBuilder().token(self.token)
            self.app = builder.build()

            async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
                if not update.message or not update.message.text:
                    return

                if update.effective_chat:
                    self.last_chat_id = update.effective_chat.id
                    if self.chat_id_cb:
                        try:
                            self.chat_id_cb(self.last_chat_id)
                        except Exception:
                            pass

                self.reset_proactive_timer()

                prompt = update.message.text.strip()

                # 1. /remember command
                if prompt.startswith("/remember"):
                    mem_text = prompt.removeprefix("/remember").strip()
                    if not mem_text:
                        await update.message.reply_text("Usage: /remember <text to save>")
                        return
                    remember(mem_text)
                    await update.message.reply_text(f"Memory saved:\n{mem_text}")
                    return

                # 2. Agentic tool commands
                cleaned_agentic_prompt = prompt
                if prompt.startswith("/search-youtube-for"):
                    cleaned_agentic_prompt = "search youtube for " + prompt.removeprefix("/search-youtube-for").strip()
                elif prompt.startswith("/search-google-for"):
                    cleaned_agentic_prompt = "search google for " + prompt.removeprefix("/search-google-for").strip()
                elif prompt.startswith("/search-giphy-for"):
                    cleaned_agentic_prompt = "search giphy for " + prompt.removeprefix("/search-giphy-for").strip()
                elif prompt.startswith("/open-browser"):
                    cleaned_agentic_prompt = "open browser"

                agentic = Agentic_Module()
                status, msg = agentic.select_tool(cleaned_agentic_prompt)
                if status and msg:
                    await update.message.reply_text(msg)
                    return

                # 3. /fetch-note-about or /write-about command
                note_prompt = None
                topic = ""
                if prompt.startswith("/fetch-note-about ") or prompt.startswith("/write-about "):
                    if prompt.startswith("/fetch-note-about "):
                        topic = prompt.removeprefix("/fetch-note-about ").strip()
                    else:
                        topic = prompt.removeprefix("/write-about ").strip()

                    llm_p, _ = write_about_prompt(topic, self.working_dir)
                    if llm_p:
                        note_prompt = llm_p
                    else:
                        await update.message.reply_text(f"No notes found matching '{topic}'.")
                        return

                # 4. Memory retrieval & note context for Ollama
                query = topic if (prompt.startswith("/fetch-note-about ") or prompt.startswith("/write-about ")) else prompt
                memories = retrieve_memories(query, limit=5)
                workspace_chunks = retrieve_workspace_chunks(query, limit=5)

                messages = []
                system_instructions = self.system_prompt
                if memories:
                    mem_block = "\n".join([f"- {m}" for m in memories])
                    system_instructions += f"\n\nRelevant past memories:\n{mem_block}"
                if workspace_chunks:
                    chunk_block = "\n\n".join([f"[{c['filename']}]\n{c['text']}" for c in workspace_chunks])
                    system_instructions += f"\n\nRelevant workspace note excerpts:\n{chunk_block}"

                messages.append({"role": "system", "content": system_instructions})
                messages.append({"role": "user", "content": note_prompt or prompt})

                try:
                    answer = await asyncio.to_thread(ollama_answer_with_model, messages, self.model_name)
                    await update.message.reply_text(answer)
                except Exception as err:
                    await update.message.reply_text(f"Error calling Ollama:\n{err}")

            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            self.app.add_handler(MessageHandler(filters.COMMAND, handle_message))

            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            self._running = True
            self._last_interaction_time = time.time()
            self._proactive_task = asyncio.create_task(self._run_proactive_loop())
            if self.notify_cb:
                self.notify_cb("Telegram bot connected and running!")
            return True
        except Exception as e:
            self._running = False
            if self.notify_cb:
                self.notify_cb(f"Telegram bot startup error: {e}")
            return False

    async def stop(self):
        self._running = False
        if self._proactive_task:
            self._proactive_task.cancel()
            try:
                await self._proactive_task
            except asyncio.CancelledError:
                pass
            self._proactive_task = None

        if self.app:
            try:
                if self.app.updater and self.app.updater.running:
                    await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()
            except Exception:
                pass
