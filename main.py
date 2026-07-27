import os
import shutil
import asyncio
import threading
from pathlib import Path
from datetime import datetime
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Markdown, Input, Select, ListView, ListItem, Label, TextArea, TabbedContent, TabPane, Checkbox, Button, DirectoryTree
from textual.binding import Binding
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.command import Provider, Hit

from langchain_ollama import OllamaLLM

import memory
from Agentic_Module import Agentic_Module
from workspace_docs import write_about_prompt, retrieve_workspace_chunks
from tgram import TelegramBotRunner

DEFAULT_SYSTEM_DESCRIPTIONS = {
    "Default": {
        "prompt": "You are a helpful AI assistant. Provide concise and accurate answers.",
        "telegram_token": "",
        "proactive_enabled": False,
        "proactive_timer": 30
    },
    "Technical Writer": {
        "prompt": "You are a professional technical documentation writer. Write clear, detailed, and structured Markdown content.",
        "telegram_token": "",
        "proactive_enabled": False,
        "proactive_timer": 30
    },
    "Creative Writer": {
        "prompt": "You are an engaging and creative writer. Craft compelling, expressive Markdown text.",
        "telegram_token": "",
        "proactive_enabled": False,
        "proactive_timer": 30
    },
    "Code Explainer": {
        "prompt": "You are an expert software engineer. Explain code and technical concepts clearly with code blocks and examples.",
        "telegram_token": "",
        "proactive_enabled": False,
        "proactive_timer": 30
    }
}

class MEditCommands(Provider):
    async def discover(self) -> None:
        yield Hit(
            1.0,
            "LLM Write",
            lambda: self.app.action_llm_write(),
            help="Ask Ollama to write something new"
        )
        yield Hit(
            1.0,
            "Compile with Ollama",
            lambda: self.app.action_compile_with_ollama(),
            help="Compile selected notes using Ollama"
        )
        yield Hit(
            1.0,
            "Manage System Descriptions",
            lambda: self.app.action_manage_system_descriptions(),
            help="Manage custom bot system descriptions and Telegram tokens"
        )
        yield Hit(
            1.0,
            "Remember Memory (/remember)",
            lambda: self.app.action_remember(),
            help="Save a memory into memory.json"
        )
        yield Hit(
            1.0,
            "Fetch Note About (/fetch-note-about)",
            lambda: self.app.action_fetch_note_about(),
            help="Fetch and interpret information about a note topic"
        )
        yield Hit(
            1.0,
            "Search YouTube (/search-youtube-for)",
            lambda: self.app.action_search_youtube(),
            help="Search YouTube in default browser"
        )
        yield Hit(
            1.0,
            "Search Google (/search-google-for)",
            lambda: self.app.action_search_google(),
            help="Search Google in default browser"
        )
        yield Hit(
            1.0,
            "Search Giphy (/search-giphy-for)",
            lambda: self.app.action_search_giphy(),
            help="Search Giphy in default browser"
        )
        yield Hit(
            1.0,
            "Open Browser (/open-browser)",
            lambda: self.app.action_open_browser(),
            help="Open default web browser"
        )
        yield Hit(
            1.0,
            "New File",
            lambda: self.app.action_new_file(),
            help="Create a new Markdown file"
        )
        yield Hit(
            1.0,
            "Create Folder",
            lambda: self.app.action_create_folder(),
            help="Create a new folder in the current directory"
        )
        yield Hit(
            1.0,
            "Delete Folder",
            lambda: self.app.action_delete_folder(),
            help="Delete a folder in the current directory"
        )
        yield Hit(
            1.0,
            "Save File",
            lambda: self.app.action_save_file(),
            help="Save the currently open file"
        )
        yield Hit(
            1.0,
            "Change Directory",
            lambda: self.app.action_change_directory(),
            help="Navigate to a different folder"
        )
        yield Hit(
            1.0,
            "Refresh Files",
            lambda: self.app.action_refresh_files(),
            help="Refresh the file list"
        )
        yield Hit(
            1.0,
            "Delete File",
            lambda: self.app.action_delete_file(),
            help="Delete the currently open file"
        )
        yield Hit(
            1.0,
            "Quit",
            lambda: self.app.action_quit(),
            help="Quit the application"
        )

    async def search(self, query: str) -> None:
        matcher = self.matcher(query)
        
        commands = [
            ("LLM Write", lambda: self.app.action_llm_write(), "Ask Ollama to write something new"),
            ("Compile with Ollama", lambda: self.app.action_compile_with_ollama(), "Compile selected notes using Ollama"),
            ("Manage System Descriptions", lambda: self.app.action_manage_system_descriptions(), "Manage custom bot system descriptions and Telegram tokens"),
            ("Remember Memory (/remember)", lambda: self.app.action_remember(), "Save a memory into memory.json"),
            ("Fetch Note About (/fetch-note-about)", lambda: self.app.action_fetch_note_about(), "Fetch and interpret information about a note topic"),
            ("Search YouTube (/search-youtube-for)", lambda: self.app.action_search_youtube(), "Search YouTube in default browser"),
            ("Search Google (/search-google-for)", lambda: self.app.action_search_google(), "Search Google in default browser"),
            ("Search Giphy (/search-giphy-for)", lambda: self.app.action_search_giphy(), "Search Giphy in default browser"),
            ("Open Browser (/open-browser)", lambda: self.app.action_open_browser(), "Open default web browser"),
            ("New File", lambda: self.app.action_new_file(), "Create a new Markdown file"),
            ("Create Folder", lambda: self.app.action_create_folder(), "Create a new folder in the current directory"),
            ("Delete Folder", lambda: self.app.action_delete_folder(), "Delete a folder in the current directory"),
            ("Save File", lambda: self.app.action_save_file(), "Save the currently open file"),
            ("Change Directory", lambda: self.app.action_change_directory(), "Navigate to a different folder"),
            ("Refresh Files", lambda: self.app.action_refresh_files(), "Refresh the file list"),
            ("Delete File", lambda: self.app.action_delete_file(), "Delete the currently open file"),
            ("Quit", lambda: self.app.action_quit(), "Quit the application"),
        ]

        for name, fn, help_text in commands:
            score = matcher.match(name)
            if score > 0:
                yield Hit(score, matcher.highlight(name), fn, help=help_text)


class NewFileScreen(ModalScreen[str]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def action_cancel(self) -> None:
        self.dismiss("")

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal_dialog"):
            yield Label("Enter new file name (e.g., notes.md):", classes="modal_label")
            yield Input(placeholder="filename.md", id="new_file_input")
            with Horizontal(classes="modal_buttons"):
                yield Button("Create", variant="primary", id="create_file")
                yield Button("Cancel", variant="error", id="cancel_file")

    def on_mount(self) -> None:
        self.query_one("#new_file_input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create_file":
            self.dismiss(self.query_one("#new_file_input", Input).value)
        else:
            self.dismiss("")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "new_file_input":
            self.dismiss(event.value)


class NewFolderScreen(ModalScreen[str]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def action_cancel(self) -> None:
        self.dismiss("")

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal_dialog"):
            yield Label("Enter new folder name:", classes="modal_label")
            yield Input(placeholder="folder_name", id="new_folder_input")
            with Horizontal(classes="modal_buttons"):
                yield Button("Create", variant="primary", id="create_folder")
                yield Button("Cancel", variant="error", id="cancel_folder")

    def on_mount(self) -> None:
        self.query_one("#new_folder_input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create_folder":
            self.dismiss(self.query_one("#new_folder_input", Input).value)
        else:
            self.dismiss("")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "new_folder_input":
            self.dismiss(event.value)


class RememberScreen(ModalScreen[str]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def action_cancel(self) -> None:
        self.dismiss("")

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal_dialog"):
            yield Label("Enter text to remember (/remember):", classes="modal_label")
            yield Input(placeholder="e.g. My cat's name is Tom and he likes salmon", id="remember_input")
            with Horizontal(classes="modal_buttons"):
                yield Button("Save Memory", variant="primary", id="save_memory")
                yield Button("Cancel", variant="error", id="cancel_memory")

    def on_mount(self) -> None:
        self.query_one("#remember_input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_memory":
            self.dismiss(self.query_one("#remember_input", Input).value)
        else:
            self.dismiss("")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "remember_input":
            self.dismiss(event.value)


class FetchNoteScreen(ModalScreen[str]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def action_cancel(self) -> None:
        self.dismiss("")

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal_dialog"):
            yield Label("Fetch note about topic (e.g. my cat named 'tom'):", classes="modal_label")
            yield Input(placeholder="e.g. my cat named tom", id="fetch_note_input")
            with Horizontal(classes="modal_buttons"):
                yield Button("Fetch & Interpret", variant="primary", id="submit_fetch")
                yield Button("Cancel", variant="error", id="cancel_fetch")

    def on_mount(self) -> None:
        self.query_one("#fetch_note_input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit_fetch":
            self.dismiss(self.query_one("#fetch_note_input", Input).value)
        else:
            self.dismiss("")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "fetch_note_input":
            self.dismiss(event.value)


class AgenticPromptScreen(ModalScreen[str]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, title: str, placeholder: str, **kwargs):
        super().__init__(**kwargs)
        self.title_str = title
        self.placeholder_str = placeholder

    def action_cancel(self) -> None:
        self.dismiss("")

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal_dialog"):
            yield Label(self.title_str, classes="modal_label")
            yield Input(placeholder=self.placeholder_str, id="agentic_input")
            with Horizontal(classes="modal_buttons"):
                yield Button("Submit", variant="primary", id="submit_agentic")
                yield Button("Cancel", variant="error", id="cancel_agentic")

    def on_mount(self) -> None:
        self.query_one("#agentic_input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit_agentic":
            self.dismiss(self.query_one("#agentic_input", Input).value)
        else:
            self.dismiss("")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "agentic_input":
            self.dismiss(event.value)


class NewSystemDescScreen(ModalScreen[tuple[str, str, str, bool, int]]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def action_cancel(self) -> None:
        self.dismiss(None)

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal_dialog_large"):
            yield Label("Create New System Description:", classes="modal_label")
            yield Label("Name (e.g., Code Reviewer):", classes="modal_label")
            yield Input(placeholder="Description name", id="new_sys_name")
            yield Label("Telegram Bot Token (Optional):", classes="modal_label")
            yield Input(placeholder="e.g. 123456789:ABCdef...", id="new_sys_token")
            yield Checkbox("Enable Proactive Conversation", id="new_sys_proactive_cb")
            yield Label("Proactive Timer (minutes):", classes="modal_label")
            yield Input(placeholder="e.g. 30", id="new_sys_proactive_timer", value="30")
            yield Label("System Prompt / Bot Behavior Instructions:", classes="modal_label")
            yield TextArea(id="new_sys_text", language="markdown")
            with Horizontal(classes="modal_buttons"):
                yield Button("Create", variant="primary", id="create_sys")
                yield Button("Cancel", variant="error", id="cancel_sys")

    def on_mount(self) -> None:
        self.query_one("#new_sys_name", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create_sys":
            name = self.query_one("#new_sys_name", Input).value.strip()
            token = self.query_one("#new_sys_token", Input).value.strip()
            text = self.query_one("#new_sys_text", TextArea).text
            proactive_enabled = self.query_one("#new_sys_proactive_cb", Checkbox).value
            timer_val = self.query_one("#new_sys_proactive_timer", Input).value.strip()
            try:
                proactive_timer = int(timer_val)
                if proactive_timer < 1:
                    proactive_timer = 1
            except ValueError:
                proactive_timer = 30
            self.dismiss((name, token, text, proactive_enabled, proactive_timer))
        else:
            self.dismiss(None)


class DeleteSystemDescScreen(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def action_cancel(self) -> None:
        self.dismiss(False)

    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)
        self.name = name

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal_dialog"):
            yield Label(f"Delete system description '{self.name}'?", classes="modal_label")
            with Horizontal(classes="modal_buttons"):
                yield Button("Yes, Delete", variant="error", id="confirm_delete_sys")
                yield Button("Cancel", variant="primary", id="cancel_delete_sys")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm_delete_sys":
            self.dismiss(True)
        else:
            self.dismiss(False)


class FolderItem(ListItem):
    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)
        self.folder_name = name

    def compose(self) -> ComposeResult:
        yield Label(f"📁 {self.folder_name}", classes="file_label")

    def on_mount(self) -> None:
        pass

class SelectFolderScreen(ModalScreen[str]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def action_cancel(self) -> None:
        self.dismiss("")

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal_dialog"):
            yield Label("Select folder to delete:", classes="modal_label")
            yield ListView(id="folder_list")
            with Horizontal(classes="modal_buttons"):
                yield Button("Cancel", variant="error", id="cancel_select")

    def on_mount(self) -> None:
        folder_list = self.query_one("#folder_list", ListView)
        try:
            for d in Path(self.app.working_directory).iterdir():
                try:
                    if d.is_dir() and not d.name.startswith("."):
                        folder_list.append(FolderItem(d.name))
                except Exception:
                    pass
        except Exception:
            pass

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, FolderItem):
            self.dismiss(event.item.folder_name)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_select":
            self.dismiss("")

class DeleteFolderScreen(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def action_cancel(self) -> None:
        self.dismiss(False)

    def __init__(self, folder_name: str, **kwargs):
        super().__init__(**kwargs)
        self.folder_name = folder_name

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal_dialog"):
            yield Label(f"Delete folder '{self.folder_name}' and ALL contents?", classes="modal_label")
            with Horizontal(classes="modal_buttons"):
                yield Button("Yes, Delete", variant="error", id="confirm_delete_folder")
                yield Button("Cancel", variant="primary", id="cancel_delete_folder")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm_delete_folder":
            self.dismiss(True)
        else:
            self.dismiss(False)


class DeleteFileScreen(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def action_cancel(self) -> None:
        self.dismiss(False)

    def __init__(self, filename: str, **kwargs):
        super().__init__(**kwargs)
        self.filename = filename

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal_dialog"):
            yield Label(f"Are you sure you want to delete '{self.filename}'?", classes="modal_label")
            with Horizontal(classes="modal_buttons"):
                yield Button("Yes, Delete", variant="error", id="confirm_delete")
                yield Button("Cancel", variant="primary", id="cancel_delete")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm_delete":
            self.dismiss(True)
        else:
            self.dismiss(False)


class LLMWriteScreen(ModalScreen[str]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def action_cancel(self) -> None:
        self.dismiss("")

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal_dialog"):
            yield Label("What would you like Ollama to write / do?", classes="modal_label")
            yield Input(placeholder="e.g. /remember Tom likes fish OR /fetch-note-about my cat OR write a summary", id="llm_prompt_input")
            with Horizontal(classes="modal_buttons"):
                yield Button("Submit", variant="primary", id="submit_prompt")
                yield Button("Cancel", variant="error", id="cancel_prompt")

    def on_mount(self) -> None:
        self.query_one("#llm_prompt_input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit_prompt":
            self.dismiss(self.query_one("#llm_prompt_input", Input).value)
        else:
            self.dismiss("")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "llm_prompt_input":
            self.dismiss(event.value)


class SystemDescriptionTab(Vertical):
    def compose(self) -> ComposeResult:
        with Vertical(id="sys_desc_container"):
            yield Label("Custom System Descriptions & Telegram Bot Settings", classes="sys_desc_header modal_label")
            with Horizontal(classes="sys_desc_buttons"):
                yield Select(
                    [(k, k) for k in DEFAULT_SYSTEM_DESCRIPTIONS.keys()],
                    prompt="Select Description",
                    id="system_tab_select",
                    allow_blank=True
                )
                yield Button("New", variant="success", id="btn_new_sys_desc")
                yield Button("Delete", variant="error", id="btn_delete_sys_desc")
            yield Label("Description Name:", classes="modal_label")
            yield Input(placeholder="System description name", id="sys_desc_name_input")
            yield Label("Telegram Bot Token (Specific to this System Description):", classes="modal_label")
            yield Input(placeholder="e.g. 123456789:ABCdef...", id="sys_desc_token_input")
            yield Label("Telegram Status: Disabled (No Token)", id="sys_desc_telegram_status", classes="modal_label")
            yield Checkbox("Enable Proactive Conversation", id="sys_desc_proactive_cb")
            yield Label("Proactive Timer (minutes):", classes="modal_label")
            yield Input(placeholder="e.g. 30", id="sys_desc_proactive_timer_input")
            yield Label("Bot System Prompt / Instructions:", classes="modal_label")
            yield TextArea(id="sys_desc_text_area", language="markdown")
            with Horizontal(classes="sys_desc_buttons"):
                yield Button("Save Changes", variant="primary", id="btn_save_sys_desc")
                yield Button("Set as Active for Bot", variant="warning", id="btn_activate_sys_desc")

    def on_mount(self) -> None:
        self.refresh_options()

    def refresh_options(self, selected_key: str | None = None) -> None:
        try:
            select = self.query_one("#system_tab_select", Select)
            descs = self.app.system_descriptions
            options = [(k, k) for k in descs.keys()]
            select.set_options(options)
            
            target = selected_key or self.app.selected_system_desc
            if target and target in descs:
                select.value = target
            elif options:
                select.value = options[0][1]
                
            self.load_selected_into_fields()
        except Exception:
            pass

    def load_selected_into_fields(self) -> None:
        try:
            select = self.query_one("#system_tab_select", Select)
            val = select.value
            if val and val != Select.BLANK and val in self.app.system_descriptions:
                self.query_one("#sys_desc_name_input", Input).value = val
                prompt = self.app.get_system_desc_prompt(val)
                token = self.app.get_system_desc_token(val)
                proactive_enabled = self.app.get_system_desc_proactive_enabled(val)
                proactive_timer = self.app.get_system_desc_proactive_timer(val)

                self.query_one("#sys_desc_token_input", Input).value = token
                self.query_one("#sys_desc_text_area", TextArea).text = prompt
                self.query_one("#sys_desc_proactive_cb", Checkbox).value = proactive_enabled
                self.query_one("#sys_desc_proactive_timer_input", Input).value = str(proactive_timer)
                
                status_lbl = self.query_one("#sys_desc_telegram_status", Label)
                if token:
                    if self.app.telegram_runner and self.app.telegram_runner._running and self.app.telegram_runner.token == token:
                        status_lbl.update("Telegram Bot Status: Connected & Running")
                    else:
                        status_lbl.update("Telegram Bot Status: Token Configured (Not Active)")
                else:
                    status_lbl.update("Telegram Bot Status: Disabled (No Token)")
        except Exception:
            pass

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "system_tab_select" and event.value != Select.BLANK:
            self.load_selected_into_fields()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_save_sys_desc":
            name = self.query_one("#sys_desc_name_input", Input).value.strip()
            token = self.query_one("#sys_desc_token_input", Input).value.strip()
            text = self.query_one("#sys_desc_text_area", TextArea).text
            proactive_enabled = self.query_one("#sys_desc_proactive_cb", Checkbox).value
            timer_str = self.query_one("#sys_desc_proactive_timer_input", Input).value.strip()
            try:
                proactive_timer = int(timer_str)
                if proactive_timer < 1:
                    proactive_timer = 1
            except ValueError:
                proactive_timer = 30

            if not name:
                self.app.notify("Description name cannot be empty!", severity="error")
                return
            old_selected = self.query_one("#system_tab_select", Select).value
            if old_selected and old_selected != Select.BLANK and old_selected != name and old_selected in self.app.system_descriptions:
                del self.app.system_descriptions[old_selected]
            
            self.app.set_system_desc(
                name,
                prompt=text,
                token=token,
                proactive_enabled=proactive_enabled,
                proactive_timer=proactive_timer
            )
            if self.app.selected_system_desc == old_selected or not self.app.selected_system_desc:
                self.app.selected_system_desc = name
                
            self.app.update_system_select_options(selected_name=name)
            self.refresh_options(selected_key=name)
            self.app.save_state()
            self.app.notify(f"Saved system description '{name}'")
            self.app.run_worker(self.app.sync_telegram_bot())

        elif event.button.id == "btn_activate_sys_desc":
            name = self.query_one("#sys_desc_name_input", Input).value.strip()
            if name in self.app.system_descriptions:
                self.app.selected_system_desc = name
                self.app.update_system_select_options(selected_name=name)
                self.app.save_state()
                self.app.notify(f"Active system description set to '{name}'")
                self.app.run_worker(self.app.sync_telegram_bot())
            else:
                self.app.notify("Please save the description before activating.", severity="warning")

        elif event.button.id == "btn_new_sys_desc":
            def check_new(result: tuple[str, str, str, bool, int] | None):
                if result:
                    name, token, text, proactive_enabled, proactive_timer = result
                    name = name.strip()
                    if not name:
                        self.app.notify("Description name cannot be empty!", severity="error")
                        return
                    self.app.set_system_desc(
                        name,
                        prompt=text,
                        token=token,
                        proactive_enabled=proactive_enabled,
                        proactive_timer=proactive_timer
                    )
                    self.app.selected_system_desc = name
                    self.app.update_system_select_options(selected_name=name)
                    self.refresh_options(selected_key=name)
                    self.app.save_state()
                    self.app.notify(f"Created system description '{name}'")
                    self.app.run_worker(self.app.sync_telegram_bot())
                    
            self.app.push_screen(NewSystemDescScreen(), check_new)

        elif event.button.id == "btn_delete_sys_desc":
            current_val = self.query_one("#system_tab_select", Select).value
            if not current_val or current_val == Select.BLANK or current_val not in self.app.system_descriptions:
                self.app.notify("No system description selected to delete.", severity="warning")
                return
                
            def check_delete(confirm: bool):
                if confirm and current_val in self.app.system_descriptions:
                    del self.app.system_descriptions[current_val]
                    if not self.app.system_descriptions:
                        self.app.set_system_desc("Default", prompt=DEFAULT_SYSTEM_DESCRIPTIONS["Default"]["prompt"], token="")
                    
                    new_active = next(iter(self.app.system_descriptions.keys()))
                    self.app.selected_system_desc = new_active
                    self.app.update_system_select_options(selected_name=new_active)
                    self.refresh_options(selected_key=new_active)
                    self.app.save_state()
                    self.app.notify(f"Deleted system description '{current_val}'")
                    self.app.run_worker(self.app.sync_telegram_bot())

            self.app.push_screen(DeleteSystemDescScreen(current_val), check_delete)


class DirItem(ListItem):
    def __init__(self, path: Path, is_parent: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.is_parent = is_parent

    def compose(self) -> ComposeResult:
        icon = "📁 "
        name = ".." if self.is_parent else self.path.name
        yield Label(f"{icon}{name}", classes="file_label")

class DirectoryBrowserTab(Vertical):
    current_path = reactive(Path.home())
    
    def compose(self) -> ComposeResult:
        yield Label(f"Current: {self.current_path}", id="current_path_label", classes="modal_label")
        yield Input(placeholder="Enter path or search directories...", id="dir_search_input")
        yield ListView(id="dir_list")
        with Horizontal(classes="modal_buttons"):
            yield Button("Set as Working Directory", variant="success", id="select_current_dir")

    def on_mount(self) -> None:
        self.current_path = Path(self.app.working_directory).resolve()
        try:
            self.query_one("#current_path_label", Label).update(f"Current: {self.current_path}")
            self.load_directories()
        except Exception as e:
            self.app.notify(f"Error in on_mount: {e}", severity="error")

    def watch_current_path(self, new_path: Path) -> None:
        try:
            self.query_one("#current_path_label", Label).update(f"Current: {new_path}")
            self.load_directories()
        except Exception as e:
            pass

    def load_directories(self, search_term: str = "") -> None:
        dir_list = self.query_one("#dir_list", ListView)
        dir_list.clear()
        
        if self.current_path.parent != self.current_path:
            dir_list.append(DirItem(self.current_path.parent, is_parent=True))
            
        try:
            dirs = []
            for d in self.current_path.iterdir():
                try:
                    if d.is_dir() and not d.name.startswith("."):
                        dirs.append(d)
                except Exception:
                    pass
            dirs.sort(key=lambda x: x.name.lower())
            
            search_lower = search_term.lower()
            for d in dirs:
                if search_lower in d.name.lower():
                    dir_list.append(DirItem(d))
        except Exception as e:
            self.app.notify(f"Error loading directories: {e}", severity="error")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, DirItem):
            self.current_path = event.item.path.resolve()
            search_input = self.query_one("#dir_search_input", Input)
            search_input.value = ""
            search_input.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "dir_search_input":
            self.load_directories(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "dir_search_input":
            value = event.input.value.strip()
            
            if value:
                try:
                    p = (self.current_path / Path(value).expanduser()).resolve()
                    if p.is_dir():
                        self.current_path = p
                        event.input.value = ""
                        return
                except Exception:
                    pass
                    
            dir_list = self.query_one("#dir_list", ListView)
            if dir_list.highlighted_child and isinstance(dir_list.highlighted_child, DirItem):
                self.current_path = dir_list.highlighted_child.path.resolve()
                event.input.value = ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "select_current_dir":
            self.app.working_directory = str(self.current_path)
            self.app.save_state()
            self.app.load_files()
            self.app.notify(f"Changed working directory to {self.current_path}")
            self.app.query_one("#tabs", TabbedContent).active = "preview_tab"
            self.app.run_worker(self.app.sync_telegram_bot())

class FileItem(ListItem):
    def __init__(self, path: Path, abs_path: Path = None, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.abs_path = abs_path or path
        
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Checkbox(classes="file_checkbox")
            yield Label(str(self.path), classes="file_label")
            
    def on_click(self, event) -> None:
        if not isinstance(event.control, Checkbox):
            self.app.open_file(self.abs_path)

class FileListView(ListView):
    BINDINGS = [
        Binding("space", "toggle_checkbox", "Toggle Select")
    ]

    def action_toggle_checkbox(self) -> None:
        if self.highlighted_child:
            checkbox = self.highlighted_child.query_one(Checkbox)
            checkbox.value = not checkbox.value

    def action_select_cursor(self) -> None:
        if self.highlighted_child:
            self.app.open_file(self.highlighted_child.abs_path)

class FileBrowser(Vertical):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search files...", id="search_input")
        yield Select(
            [
                ("Name (A-Z)", "name"), 
                ("Name (Z-A)", "name_rev"), 
                ("Date (Newest First)", "date"),
                ("Date (Oldest First)", "date_asc")
            ],
            value="name",
            id="sort_select",
            allow_blank=False
        )
        yield Select(
            [],
            prompt="Loading models...",
            id="model_select",
            allow_blank=True
        )
        yield Select(
            [(k, k) for k in DEFAULT_SYSTEM_DESCRIPTIONS.keys()],
            prompt="System Description...",
            id="system_select",
            allow_blank=True
        )
        yield FileListView(id="file_list")

class MEditApp(App):
    TITLE = "m-edit"

    def safe_call_from_thread(self, callback, *args, **kwargs):
        if threading.get_ident() == getattr(self, "_thread_id", None):
            return callback(*args, **kwargs)
        try:
            return self.call_from_thread(callback, *args, **kwargs)
        except RuntimeError:
            return callback(*args, **kwargs)
    CSS = """
    Screen {
        layout: horizontal;
    }
    
    FileBrowser {
        width: 35;
        dock: left;
        border-right: solid $primary-background;
    }
    
    #file_list, #dir_list {
        height: 1fr;
    }
    
    #editor_pane {
        width: 1fr;
        height: 1fr;
    }
    
    TabbedContent {
        height: 1fr;
    }
    
    Markdown {
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
    }
    
    .file_label {
        padding-top: 1;
        padding-left: 1;
    }
    
    .modal_dialog {
        padding: 2 4;
        margin: 4 8;
        background: $surface;
        border: thick $primary;
        height: auto;
        width: 60;
        align: center middle;
    }
    
    .modal_dialog_large {
        padding: 2 4;
        margin: 4 8;
        background: $surface;
        border: thick $primary;
        height: 80%;
        width: 80%;
        align: center middle;
    }
    
    .modal_label {
        margin-bottom: 1;
    }
    
    .modal_buttons {
        margin-top: 2;
        height: auto;
        align: center middle;
    }
    
    .modal_buttons Button {
        margin: 0 1;
    }

    SystemDescriptionTab {
        height: 1fr;
        overflow-y: auto;
    }

    #sys_desc_container {
        padding: 1 2;
        height: auto;
    }

    .sys_desc_header {
        margin-bottom: 1;
    }

    .sys_desc_buttons {
        margin-top: 1;
        margin-bottom: 1;
        height: auto;
    }

    .sys_desc_buttons Button {
        margin-right: 1;
    }

    #sys_desc_text_area {
        height: 15;
        min-height: 10;
        margin-top: 1;
    }
    """
    
    COMMANDS: ClassVar[set[type[Provider] | Provider]] = App.COMMANDS | {MEditCommands}
    
    BINDINGS = [
        Binding("ctrl+p", "command_palette", "Palette"),
    ]

    current_file = reactive(None)
    working_directory = reactive(str(Path.cwd()))
    selected_system_desc = "Default"
    system_descriptions = DEFAULT_SYSTEM_DESCRIPTIONS.copy()
    telegram_runner = None

    def get_system_desc_prompt(self, name: str) -> str:
        val = self.system_descriptions.get(name, "")
        if isinstance(val, dict):
            return val.get("prompt", "")
        return str(val)

    def get_system_desc_token(self, name: str) -> str:
        val = self.system_descriptions.get(name, "")
        if isinstance(val, dict):
            return val.get("telegram_token", "")
        return ""

    def get_system_desc_proactive_enabled(self, name: str) -> bool:
        val = self.system_descriptions.get(name, "")
        if isinstance(val, dict):
            return bool(val.get("proactive_enabled", False))
        return False

    def get_system_desc_proactive_timer(self, name: str) -> int:
        val = self.system_descriptions.get(name, "")
        if isinstance(val, dict):
            try:
                return int(val.get("proactive_timer", 30))
            except (ValueError, TypeError):
                return 30
        return 30

    def get_system_desc_last_chat_id(self, name: str) -> int | None:
        val = self.system_descriptions.get(name, "")
        if isinstance(val, dict):
            return val.get("last_chat_id", None)
        return None

    def set_system_desc(
        self,
        name: str,
        prompt: str,
        token: str = "",
        proactive_enabled: bool = False,
        proactive_timer: int = 30,
        last_chat_id: int | None = None
    ):
        existing = self.system_descriptions.get(name, {})
        if not isinstance(existing, dict):
            existing = {}
        if last_chat_id is None:
            last_chat_id = existing.get("last_chat_id", None)
        self.system_descriptions[name] = {
            "prompt": prompt,
            "telegram_token": token,
            "proactive_enabled": proactive_enabled,
            "proactive_timer": proactive_timer,
            "last_chat_id": last_chat_id
        }

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield FileBrowser()
            with Vertical(id="editor_pane"):
                with TabbedContent(id="tabs"):
                    with TabPane("Preview", id="preview_tab"):
                        yield Markdown("Select a file to preview or edit. Use Ctrl+P for AI commands.", id="markdown_viewer")
                    with TabPane("Edit", id="edit_tab"):
                        yield TextArea(id="text_editor", language="markdown")
                    with TabPane("System Prompts", id="system_tab"):
                        yield SystemDescriptionTab()
                    with TabPane("Folders", id="folders_tab"):
                        yield DirectoryBrowserTab()
        yield Footer()

    def on_mount(self) -> None:
        self.load_state()
        
        search_val = getattr(self, "_initial_search", "")
        sort_val = getattr(self, "_initial_sort", "name")
        
        try:
            self.query_one("#search_input", Input).value = search_val
            self.query_one("#sort_select", Select).value = sort_val
        except Exception:
            pass
            
        self.update_system_select_options(selected_name=self.selected_system_desc)
        self.load_files(search_term=search_val, sort_by=sort_val)
        self.run_worker(self.load_ollama_models())
        self.run_worker(self.sync_telegram_bot())

    async def sync_telegram_bot(self) -> None:
        active_name = self.selected_system_desc
        token = self.get_system_desc_token(active_name)
        prompt = self.get_system_desc_prompt(active_name)
        proactive_enabled = self.get_system_desc_proactive_enabled(active_name)
        proactive_timer = self.get_system_desc_proactive_timer(active_name)
        last_chat_id = self.get_system_desc_last_chat_id(active_name)

        model_name = "llama3"
        try:
            model_val = self.query_one("#model_select", Select).value
            if model_val and model_val != Select.BLANK:
                model_name = model_val
        except Exception:
            pass

        if self.telegram_runner:
            if self.telegram_runner.token == token and self.telegram_runner._running:
                self.telegram_runner.system_prompt = prompt
                self.telegram_runner.working_dir = self.working_directory
                self.telegram_runner.model_name = model_name
                self.telegram_runner.update_proactive_settings(proactive_enabled, proactive_timer)
                if last_chat_id and not self.telegram_runner.last_chat_id:
                    self.telegram_runner.last_chat_id = last_chat_id
                return
            else:
                await self.telegram_runner.stop()
                self.telegram_runner = None

        if token:
            def notify_cb(msg: str):
                self.safe_call_from_thread(self.notify, msg)

            def chat_id_cb(chat_id: int):
                active = self.selected_system_desc
                if active in self.system_descriptions and isinstance(self.system_descriptions[active], dict):
                    self.system_descriptions[active]["last_chat_id"] = chat_id
                    self.safe_call_from_thread(self.save_state)

            runner = TelegramBotRunner(
                token=token,
                system_prompt=prompt,
                model_name=model_name,
                working_dir=self.working_directory,
                notify_cb=notify_cb,
                proactive_enabled=proactive_enabled,
                proactive_timer=proactive_timer,
                last_chat_id=last_chat_id,
                chat_id_cb=chat_id_cb
            )
            self.telegram_runner = runner
            started = await runner.start()
            if started:
                self.notify(f"Telegram bot connected for '{active_name}'")
            else:
                self.notify("Telegram bot token failed to connect.", severity="error")

            try:
                sys_tab = self.query_one(SystemDescriptionTab)
                sys_tab.load_selected_into_fields()
            except Exception:
                pass

    def update_system_select_options(self, selected_name: str | None = None) -> None:
        try:
            system_select = self.query_one("#system_select", Select)
            options = [(name, name) for name in self.system_descriptions.keys()]
            system_select.set_options(options)
            target = selected_name or self.selected_system_desc
            if target and target in self.system_descriptions:
                system_select.value = target
            elif options:
                system_select.value = options[0][1]
                self.selected_system_desc = options[0][1]
        except Exception:
            pass

    def load_state(self) -> None:
        import platformdirs
        import json
        config_dir = Path(platformdirs.user_data_dir("m-edit"))
        config_file = config_dir / "config.json"
        
        if not config_file.exists():
            try:
                config_dir.mkdir(parents=True, exist_ok=True)
                default_data = {
                    "working_directory": str(Path.cwd()),
                    "search_term": "",
                    "sort_by": "name",
                    "selected_model": "",
                    "selected_system_desc": "Default",
                    "system_descriptions": DEFAULT_SYSTEM_DESCRIPTIONS
                }
                config_file.write_text(json.dumps(default_data, indent=2))
            except Exception:
                pass

        if config_file.exists():
            try:
                data = json.loads(config_file.read_text())
                saved_dir = data.get("working_directory")
                if saved_dir and Path(saved_dir).is_dir():
                    self.working_directory = saved_dir
                self._initial_search = data.get("search_term", "")
                self._initial_sort = data.get("sort_by", "name")
                self._initial_model = data.get("selected_model", "")
                self.selected_system_desc = data.get("selected_system_desc", "Default")
                descs = data.get("system_descriptions")
                if isinstance(descs, dict) and descs:
                    self.system_descriptions = descs
                else:
                    self.system_descriptions = DEFAULT_SYSTEM_DESCRIPTIONS.copy()
            except Exception:
                self._initial_search = ""
                self._initial_sort = "name"
                self._initial_model = ""
                self.selected_system_desc = "Default"
                self.system_descriptions = DEFAULT_SYSTEM_DESCRIPTIONS.copy()
        else:
            self._initial_search = ""
            self._initial_sort = "name"
            self._initial_model = ""
            self.selected_system_desc = "Default"
            self.system_descriptions = DEFAULT_SYSTEM_DESCRIPTIONS.copy()

    def save_state(self) -> None:
        import platformdirs
        import json
        config_dir = Path(platformdirs.user_data_dir("m-edit"))
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.json"
        
        try:
            search_val = self.query_one("#search_input", Input).value
        except Exception:
            search_val = getattr(self, "_initial_search", "")
            
        try:
            sort_val = self.query_one("#sort_select", Select).value
        except Exception:
            sort_val = getattr(self, "_initial_sort", "name")

        try:
            model_val = self.query_one("#model_select", Select).value
        except Exception:
            model_val = getattr(self, "_initial_model", "")

        try:
            sys_val = self.query_one("#system_select", Select).value
            if sys_val != Select.BLANK:
                self.selected_system_desc = sys_val
        except Exception:
            pass
            
        try:
            config_data = {
                "working_directory": self.working_directory,
                "search_term": search_val,
                "sort_by": sort_val,
                "selected_model": model_val if model_val != Select.BLANK else "",
                "selected_system_desc": self.selected_system_desc,
                "system_descriptions": self.system_descriptions
            }
            config_file.write_text(json.dumps(config_data, indent=2))
        except Exception as e:
            self.notify(f"Error saving state: {e}", severity="warning")

    async def load_ollama_models(self) -> None:
        import ollama
        try:
            models_list = await asyncio.to_thread(ollama.list)
            if hasattr(models_list, 'models'):
                models = [(m.model, m.model) for m in models_list.models]
            else:
                models = [(m['name'], m['name']) for m in models_list.get('models', [])]
                
            if not models:
                models = [("llama3 (not found)", "llama3")]
        except Exception:
            models = [("llama3 (error connecting)", "llama3")]
            
        select = self.query_one("#model_select", Select)
        select.set_options(models)
        
        saved_model = getattr(self, "_initial_model", None)
        model_values = [m[1] for m in models]
        if saved_model and saved_model in model_values:
            select.value = saved_model
        elif models:
            select.value = models[0][1]

    _search_task_id = 0

    def load_files(self, search_term: str = "", sort_by: str = "name") -> None:
        self._search_task_id += 1
        self.run_worker(self._load_files_async(self.working_directory, search_term, sort_by, self._search_task_id))

    async def _load_files_async(self, working_directory: str, search_term: str, sort_by: str, task_id: int) -> None:
        def do_search():
            paths = []
            for root, dirs, files in os.walk(working_directory):
                if self._search_task_id != task_id: return None
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["venv", ".venv", "node_modules", "target", "build", "dist"]]
                for file in files:
                    if file.endswith(".md"):
                        paths.append(Path(root) / file)
                        
            if search_term:
                filtered_paths = []
                search_lower = search_term.lower()
                for p in paths:
                    if self._search_task_id != task_id: return None
                    if search_lower in p.name.lower():
                        filtered_paths.append(p)
                    else:
                        try:
                            content = p.read_text(errors='ignore')
                            if search_lower in content.lower():
                                filtered_paths.append(p)
                        except Exception:
                            pass
                paths = filtered_paths
                
            if sort_by == "name":
                paths.sort(key=lambda p: p.name.lower())
            elif sort_by == "name_rev":
                paths.sort(key=lambda p: p.name.lower(), reverse=True)
            elif sort_by == "date":
                paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            elif sort_by == "date_asc":
                paths.sort(key=lambda p: p.stat().st_mtime)
            return paths

        paths = await asyncio.to_thread(do_search)
        
        if paths is not None and self._search_task_id == task_id:
            file_list = self.query_one("#file_list", FileListView)
            file_list.clear()
            items = []
            for p in paths:
                try:
                    rel_path = p.relative_to(Path(working_directory))
                    items.append(FileItem(path=rel_path, abs_path=p))
                except ValueError:
                    items.append(FileItem(path=p, abs_path=p))
            for item in items:
                file_list.append(item)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search_input":
            sort_val = self.query_one("#sort_select", Select).value
            self.load_files(search_term=event.value, sort_by=sort_val)
            self.save_state()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "sort_select":
            search_val = self.query_one("#search_input", Input).value
            self.load_files(search_term=search_val, sort_by=event.value)
            self.save_state()
        elif event.select.id == "model_select":
            self.save_state()
            self.run_worker(self.sync_telegram_bot())
        elif event.select.id == "system_select":
            if event.value != Select.BLANK:
                self.selected_system_desc = event.value
                try:
                    sys_tab = self.query_one(SystemDescriptionTab)
                    sys_tab.refresh_options(selected_key=event.value)
                except Exception:
                    pass
                self.save_state()
                self.run_worker(self.sync_telegram_bot())

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        pass

    def open_file(self, path: Path) -> None:
        self.current_file = path
        try:
            content = path.read_text()
            self.query_one("#markdown_viewer", Markdown).update(content)
            self.query_one("#text_editor", TextArea).text = content
            self.sub_title = str(path)
        except Exception as e:
            self.notify(f"Error opening file: {e}", severity="error")

    def action_save_file(self) -> None:
        content = self.query_one("#text_editor", TextArea).text
        if self.current_file:
            try:
                self.current_file.write_text(content)
                self.query_one("#markdown_viewer", Markdown).update(content)
                self.notify(f"Saved {self.current_file}")
            except Exception as e:
                self.notify(f"Error saving file: {e}", severity="error")
        else:
            new_file_path = Path(f"ai_generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
            try:
                new_file_path.write_text(content)
                self.current_file = new_file_path
                self.sub_title = str(new_file_path)
                self.query_one("#markdown_viewer", Markdown).update(content)
                self.notify(f"Saved as {new_file_path}")
                self.load_files()
            except Exception as e:
                self.notify(f"Error saving new file: {e}", severity="error")

    def action_refresh_files(self) -> None:
        search_val = self.query_one("#search_input", Input).value
        sort_val = self.query_one("#sort_select", Select).value
        self.load_files(search_term=search_val, sort_by=sort_val)

    def action_change_directory(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "folders_tab"
        self.query_one("#dir_search_input", Input).focus()

    def action_manage_system_descriptions(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "system_tab"

    def action_remember(self) -> None:
        def save_mem(text: str | None) -> None:
            if text and text.strip():
                memory.remember(text.strip())
                self.notify(f"Saved memory: {text.strip()}")
        self.push_screen(RememberScreen(), save_mem)

    def action_fetch_note_about(self) -> None:
        def do_fetch(topic: str | None) -> None:
            if topic and topic.strip():
                model_name = self.query_one("#model_select", Select).value
                self.run_worker(self.generate_llm_content(f"/fetch-note-about {topic.strip()}", model_name), thread=True)
        self.push_screen(FetchNoteScreen(), do_fetch)

    def action_search_youtube(self) -> None:
        def do_search(query: str | None) -> None:
            if query and query.strip():
                agentic = Agentic_Module()
                status, msg = agentic.select_tool(f"search youtube for {query.strip()}")
                self.notify(msg or f"Searching YouTube for {query}")
        self.push_screen(AgenticPromptScreen("Search YouTube for:", "e.g. cute cats"), do_search)

    def action_search_google(self) -> None:
        def do_search(query: str | None) -> None:
            if query and query.strip():
                agentic = Agentic_Module()
                status, msg = agentic.select_tool(f"search google for {query.strip()}")
                self.notify(msg or f"Searching Google for {query}")
        self.push_screen(AgenticPromptScreen("Search Google for:", "e.g. python textual docs"), do_search)

    def action_search_giphy(self) -> None:
        def do_search(query: str | None) -> None:
            if query and query.strip():
                agentic = Agentic_Module()
                status, msg = agentic.select_tool(f"search giphy for {query.strip()}")
                self.notify(msg or f"Searching Giphy for {query}")
        self.push_screen(AgenticPromptScreen("Search Giphy for:", "e.g. happy cat"), do_search)

    def action_open_browser(self) -> None:
        agentic = Agentic_Module()
        status, msg = agentic.select_tool("open browser")
        self.notify(msg or "Opening web browser")

    def action_delete_file(self) -> None:
        if not self.current_file:
            self.notify("No file is currently open to delete.", severity="warning")
            return
            
        def check_reply(confirm: bool) -> None:
            if confirm and self.current_file:
                try:
                    self.current_file.unlink()
                    self.notify(f"Deleted {self.current_file.name}", severity="information")
                    self.current_file = None
                    self.sub_title = ""
                    self.query_one("#markdown_viewer", Markdown).update("Select a file to preview or edit. Use Ctrl+P for AI commands.")
                    self.query_one("#text_editor", TextArea).text = ""
                    self.load_files()
                except Exception as e:
                    self.notify(f"Error deleting file: {e}", severity="error")
                    
        self.push_screen(DeleteFileScreen(self.current_file.name), check_reply)

    def action_new_file(self) -> None:
        def check_reply(filename: str | None) -> None:
            if filename:
                if not filename.endswith('.md'):
                    filename += '.md'
                new_path = Path(self.working_directory) / filename
                if new_path.exists():
                    self.notify(f"File {filename} already exists!", severity="error")
                    return
                try:
                    new_path.write_text("")
                    self.load_files()
                    self.open_file(new_path)
                    self.query_one("#tabs", TabbedContent).active = "edit_tab"
                    self.query_one("#text_editor", TextArea).focus()
                    self.notify(f"Created {filename}")
                except Exception as e:
                    self.notify(f"Error creating file: {e}", severity="error")
        self.push_screen(NewFileScreen(), check_reply)

    def action_create_folder(self) -> None:
        def check_reply(folder_name: str | None) -> None:
            if folder_name:
                new_path = Path(self.working_directory) / folder_name
                if new_path.exists():
                    self.notify(f"Folder '{folder_name}' already exists!", severity="error")
                    return
                try:
                    new_path.mkdir(parents=True)
                    self.notify(f"Created folder '{folder_name}'")
                    self.load_files()
                except Exception as e:
                    self.notify(f"Error creating folder: {e}", severity="error")
        self.push_screen(NewFolderScreen(), check_reply)

    def action_delete_folder(self) -> None:
        def check_delete_confirm(confirm: bool, folder_name: str) -> None:
            if confirm:
                target_path = Path(self.working_directory) / folder_name
                try:
                    shutil.rmtree(target_path)
                    self.notify(f"Deleted folder '{folder_name}'", severity="information")
                    self.load_files()
                except Exception as e:
                    self.notify(f"Error deleting folder: {e}", severity="error")

        def check_folder_select(folder_name: str | None) -> None:
            if folder_name:
                self.push_screen(DeleteFolderScreen(folder_name), lambda c: check_delete_confirm(c, folder_name))

        self.push_screen(SelectFolderScreen(), check_folder_select)

    def action_llm_write(self) -> None:
        model_name = self.query_one("#model_select", Select).value
        def check_reply(prompt: str | None) -> None:
            if prompt:
                self.run_worker(self.generate_llm_content(prompt, model_name), thread=True)
        self.push_screen(LLMWriteScreen(), check_reply)

    def action_compile_with_ollama(self) -> None:
        model_name = self.query_one("#model_select", Select).value
        selected_files = []
        for item in self.query(FileItem):
            checkbox = item.query_one(Checkbox)
            if checkbox.value:
                selected_files.append(item.abs_path)
                
        if not selected_files:
            self.notify("No files selected!", severity="warning")
            return
            
        self.run_worker(self.compile_files(selected_files, model_name), thread=True)

    async def generate_llm_content(self, prompt: str, model_name: str) -> None:
        self.safe_call_from_thread(self.notify, f"Processing with {model_name}...", timeout=3)
        try:
            # 1. Check for /remember command
            if prompt.startswith("/remember"):
                mem_text = prompt.removeprefix("/remember").strip()
                if mem_text:
                    memory.remember(mem_text)
                    self.safe_call_from_thread(self.notify, f"Memory saved: {mem_text}")
                    self.safe_call_from_thread(self.show_generated_content, f"**Memory Saved:**\n{mem_text}")
                    return

            # 2. Check for Agentic module tools
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
            status, agentic_msg = agentic.select_tool(cleaned_agentic_prompt)
            if status and agentic_msg:
                self.safe_call_from_thread(self.notify, agentic_msg)
                self.safe_call_from_thread(self.show_generated_content, f"**Agentic Action:** {agentic_msg}")
                return

            # 3. Check for /fetch-note-about or /write-about
            note_prompt = None
            if prompt.startswith("/fetch-note-about ") or prompt.startswith("/write-about "):
                if prompt.startswith("/fetch-note-about "):
                    topic = prompt.removeprefix("/fetch-note-about ").strip()
                else:
                    topic = prompt.removeprefix("/write-about ").strip()

                llm_p, _ = write_about_prompt(topic, self.working_directory)
                if llm_p:
                    note_prompt = llm_p
                else:
                    self.safe_call_from_thread(self.notify, f"No notes found for '{topic}'", severity="warning")
                    self.safe_call_from_thread(self.show_generated_content, f"No notes found in workspace for topic '{topic}'.")
                    return

            # 4. Memory retrieval & note context for Ollama query
            actual_query = prompt
            if prompt.startswith("/fetch-note-about "):
                actual_query = prompt.removeprefix("/fetch-note-about ").strip()
            elif prompt.startswith("/write-about "):
                actual_query = prompt.removeprefix("/write-about ").strip()

            memories = memory.retrieve_memories(actual_query, limit=5)
            workspace_chunks = retrieve_workspace_chunks(actual_query, limit=5)

            system_text = self.get_system_desc_prompt(self.selected_system_desc)
            if memories:
                mem_block = "\n".join([f"- {m}" for m in memories])
                system_text += f"\n\nRelevant past memories:\n{mem_block}"
            if workspace_chunks:
                chunk_block = "\n\n".join([f"[{c['filename']}]\n{c['text']}" for c in workspace_chunks])
                system_text += f"\n\nRelevant workspace note excerpts:\n{chunk_block}"

            if system_text:
                full_prompt = f"System Instructions:\n{system_text}\n\nUser Request:\n{note_prompt or prompt}"
            else:
                full_prompt = note_prompt or prompt
                
            llm = OllamaLLM(model=model_name)
            response = await asyncio.to_thread(llm.invoke, full_prompt)
            self.safe_call_from_thread(self.show_generated_content, response)
        except Exception as e:
            self.safe_call_from_thread(self.notify, f"LLM Error: {e}", severity="error")

    async def compile_files(self, files: list[Path], model_name: str) -> None:
        self.safe_call_from_thread(self.notify, f"Compiling {len(files)} files with {model_name}...", timeout=3)
        try:
            content = ""
            for p in files:
                content += f"\n\n--- File: {p} ---\n{p.read_text(errors='ignore')}"
                
            system_text = self.get_system_desc_prompt(self.selected_system_desc)
            memories = memory.retrieve_memories("compile notes article", limit=5)
            if memories:
                mem_block = "\n".join([f"- {m}" for m in memories])
                system_text += f"\n\nRelevant past memories:\n{mem_block}"

            if system_text:
                prompt = f"System Instructions:\n{system_text}\n\nCompile the following notes into a cohesive article. Write only the article content in Markdown format:\n{content}"
            else:
                prompt = f"Compile the following notes into a cohesive article. Write only the article content in Markdown format:\n{content}"
            
            llm = OllamaLLM(model=model_name)
            response = await asyncio.to_thread(llm.invoke, prompt)
            self.safe_call_from_thread(self.show_generated_content, response)
        except Exception as e:
            self.safe_call_from_thread(self.notify, f"LLM Error: {e}", severity="error")

    def show_generated_content(self, text: str) -> None:
        self.current_file = None
        self.sub_title = "Unsaved AI Generation (Ctrl+S to save)"
        self.query_one("#markdown_viewer", Markdown).update(text)
        self.query_one("#text_editor", TextArea).text = text
        self.notify("Generation complete!", severity="information")

def main():
    app = MEditApp()
    app.run()

if __name__ == "__main__":
    main()
