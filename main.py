import os
import shutil
import asyncio
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
        
        score = matcher.match("LLM Write")
        if score > 0:
            yield Hit(
                score,
                matcher.highlight("LLM Write"),
                lambda: self.app.action_llm_write(),
                help="Ask Ollama to write something new"
            )
            
        score = matcher.match("Compile with Ollama")
        if score > 0:
            yield Hit(
                score,
                matcher.highlight("Compile with Ollama"),
                lambda: self.app.action_compile_with_ollama(),
                help="Compile selected notes using Ollama"
            )
            
        score = matcher.match("New File")
        if score > 0:
            yield Hit(
                score,
                matcher.highlight("New File"),
                lambda: self.app.action_new_file(),
                help="Create a new Markdown file"
            )

        score = matcher.match("Create Folder")
        if score > 0:
            yield Hit(
                score,
                matcher.highlight("Create Folder"),
                lambda: self.app.action_create_folder(),
                help="Create a new folder in the current directory"
            )

        score = matcher.match("Delete Folder")
        if score > 0:
            yield Hit(
                score,
                matcher.highlight("Delete Folder"),
                lambda: self.app.action_delete_folder(),
                help="Delete a folder in the current directory"
            )

        score = matcher.match("Save File")
        if score > 0:
            yield Hit(
                score,
                matcher.highlight("Save File"),
                lambda: self.app.action_save_file(),
                help="Save the currently open file"
            )

        score = matcher.match("Change Directory")
        if score > 0:
            yield Hit(
                score,
                matcher.highlight("Change Directory"),
                lambda: self.app.action_change_directory(),
                help="Navigate to a different folder"
            )

        score = matcher.match("Refresh Files")
        if score > 0:
            yield Hit(
                score,
                matcher.highlight("Refresh Files"),
                lambda: self.app.action_refresh_files(),
                help="Refresh the file list"
            )

        score = matcher.match("Delete File")
        if score > 0:
            yield Hit(
                score,
                matcher.highlight("Delete File"),
                lambda: self.app.action_delete_file(),
                help="Delete the currently open file"
            )

        score = matcher.match("Quit")
        if score > 0:
            yield Hit(
                score,
                matcher.highlight("Quit"),
                lambda: self.app.action_quit(),
                help="Quit the application"
            )


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


class FolderItem(ListItem):
    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)
        self.folder_name = name

    def compose(self) -> ComposeResult:
        yield Label(f"📁 {self.folder_name}", classes="file_label")

    def on_mount(self) -> None:
        # Fixed typo dynamically or correctly below
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
            yield Label("What would you like Ollama to write?", classes="modal_label")
            yield Input(placeholder="Enter your prompt here...", id="llm_prompt_input")
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
        # Bypass the default selection mechanism which might be blocked by Checkbox
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
        yield FileListView(id="file_list")

class MEditApp(App):
    TITLE = "m-edit"
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
    """
    
    COMMANDS: ClassVar[set[type[Provider] | Provider]] = App.COMMANDS | {MEditCommands}
    
    BINDINGS = [
        Binding("ctrl+p", "command_palette", "Palette"),
    ]

    current_file = reactive(None)
    working_directory = reactive(str(Path.cwd()))
    
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
            
        self.load_files(search_term=search_val, sort_by=sort_val)
        self.run_worker(self.load_ollama_models())

    def load_state(self) -> None:
        import platformdirs
        import json
        config_dir = Path(platformdirs.user_data_dir("m-edit"))
        config_file = config_dir / "config.json"
        if config_file.exists():
            try:
                data = json.loads(config_file.read_text())
                saved_dir = data.get("working_directory")
                if saved_dir and Path(saved_dir).is_dir():
                    self.working_directory = saved_dir
                self._initial_search = data.get("search_term", "")
                self._initial_sort = data.get("sort_by", "name")
            except Exception:
                self._initial_search = ""
                self._initial_sort = "name"
        else:
            self._initial_search = ""
            self._initial_sort = "name"

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
            config_file.write_text(json.dumps({
                "working_directory": self.working_directory,
                "search_term": search_val,
                "sort_by": sort_val
            }))
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
        if models:
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
            # Append all items without blocking too much
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
            # Generate a new file name based on time
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
        self.call_from_thread(self.notify, f"Generating with {model_name}...", timeout=3)
        try:
            llm = OllamaLLM(model=model_name)
            response = await asyncio.to_thread(llm.invoke, prompt)
            self.call_from_thread(self.show_generated_content, response)
        except Exception as e:
            self.call_from_thread(self.notify, f"LLM Error: {e}", severity="error")

    async def compile_files(self, files: list[Path], model_name: str) -> None:
        self.call_from_thread(self.notify, f"Compiling {len(files)} files with {model_name}...", timeout=3)
        try:
            content = ""
            for p in files:
                content += f"\n\n--- File: {p} ---\n{p.read_text(errors='ignore')}"
                
            prompt = f"Compile the following notes into a cohesive article. Write only the article content in Markdown format:\n{content}"
            
            llm = OllamaLLM(model=model_name)
            response = await asyncio.to_thread(llm.invoke, prompt)
            self.call_from_thread(self.show_generated_content, response)
        except Exception as e:
            self.call_from_thread(self.notify, f"LLM Error: {e}", severity="error")

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
