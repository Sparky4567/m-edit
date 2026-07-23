# m-edit

`m-edit` is a terminal-based Markdown viewer and editor, inspired by tools like `glow`, built with Python and [Textual](https://textual.textualize.io/). It features a persistent file manager to seamlessly switch between workspaces, real-time search, sorting capabilities, a split-pane layout for rendering and editing Markdown files, and **local AI integration powered by Ollama and Langchain!**

## Requirements

To use the AI features, you must have the `ollama` daemon installed and running locally on your machine, with the `llama3` model pulled:

```bash
# Start the Ollama server in the background (if not already running)
ollama serve

# Pull the default model (or any other model you prefer)
ollama run llama3
```

> **Note:** `m-edit` automatically queries your local Ollama daemon to fetch your installed models. You can select which model to use via the dropdown menu in the left file browser pane!

## Installation

This project is managed by `uv`. If you don't have `uv` installed, you can install it following the instructions at [astral.sh/uv](https://github.com/astral-sh/uv).

Once `uv` is installed, you can initialize the environment and install dependencies automatically when you run the app.

## How to Use

To launch the editor, navigate to the project directory and run:

```bash
uv run m-edit
```

### Navigating the Interface

*   **Left Pane (File Browser):** 
    *   **Search Files:** Start typing in the search bar to filter the file list. The search looks through both the file names and the contents of the Markdown files.
    *   **Sort Files:** Use the dropdown menu below the search bar to sort files either alphabetically (A-Z) or by the newest modification date.
    *   **Select Model:** A dropdown under the sort menu lists all available Ollama models installed on your machine. Pick your favorite!
    *   **Select Multiple Files:** Click the checkboxes next to files (or hit `Space` while focused on a checkbox) to select multiple files for AI compilation.
    *   **Open File:** Use your arrow keys (`↑` and `↓`) or the mouse to navigate the file list and hit `Enter` on the file name to open it.
*   **Right Pane (Editor/Viewer):**
    *   **Preview Tab:** Displays the richly rendered Markdown of the currently selected file. You can click on the tab at the top to switch to it.
    *   **Edit Tab:** A text editor where you can make changes to the Markdown source. 
    *   **Folders Tab:** A built-in directory browser to explore your file system. You can type absolute or relative paths to instantly jump between folders, and click "Set as Working Directory" to load its contents into the sidebar. 

### Keyboard Shortcuts & Commands

*   **`Ctrl+P`**: **Open the Command Palette.** From here you can access all application actions:
    *   **`Change Directory`**: Switches to the Folders tab where you can navigate to a new directory. `m-edit` will automatically remember your last opened folder across sessions!
    *   **`Create Folder`**: Prompts you for a folder name and creates a new directory inside your current working space.
    *   **`Delete Folder`**: Opens a dialog to permanently delete a folder and all of its contents (with safety confirmation).
    *   **`New File`**: Opens a prompt to enter a filename, creates an empty `.md` file, and opens it directly in the editor.
    *   **`Save File`**: Saves the currently open file. If it is a new AI generation without a filename, it will be saved with an auto-generated timestamp filename.
    *   **`Delete File`**: Opens a confirmation dialog to delete the currently open file from the disk permanently.
    *   **`Refresh Files`**: Refreshes the file list (useful if files were added or modified outside of the editor).
    *   **`Quit`**: Quits the application.
    *   **`LLM Write`**: Opens a prompt dialog. Ask Ollama to write a new article or snippet for you.
    *   **`Compile with Ollama`**: Takes all the files you've checked in the file browser and asks Ollama to compile them into a single cohesive article.
*   **`Tab` / `Shift+Tab`**: Cycle keyboard focus between the search bar, sort dropdown, file list, and the tabs.
