import json
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus

from workspace_docs import list_workspaces

APP_SETTINGS_FILE = Path("app_settings.json")


class Agentic_Module:
    
    def __init__(self, browser_opener=None):
        self.default_browser_address = "https://www.google.com/"
        self.default_web_url = "https://www.google.com"
        self.youtube_url = "https://www.youtube.com/"
        self.google_url = "https://www.google.com/"
        self.gpt_url = "https://chat.openai.com/"
        self.giphy_url = "https://giphy.com/"
        self.default_status = None
        self.browser_opener = browser_opener or webbrowser.open_new_tab

    def message_handler(self, message_to_return):
        return message_to_return
    
    def return_status(self, status):
        self.default_status = status
        return self.default_status
    
    def open_url(self, url):
        self.browser_opener(url)
    
    def open_browser (self):
        self.open_url(self.default_browser_address)

    # Youtube Search
    # words: list of words to identify the command
    # sentence: full user input
    # passed_url: base url to use for the search
    # Example: words = ["search","youtube","for"], sentence = "search youtube for cute cats", passed_url = "https://www.youtube.com/"
    # Look at the example above, if all words in the list are found in the sentence, the function will extract the search terms (cute cats) and open a new tab with the search results on YouTube.
    # The function constructs the search URL by appending the search terms to the base URL.
    # The search terms are joined with '+' to form a valid query string.
    # Finally, it opens a new browser tab with the constructed URL.
    # This function can be adapted for other search engines by changing the base URL and the command words.
    # Example for Google: words = ["search","google","for"], passed_url = "https://www.google.com/"
    # Look at init functions below for usage examples.
    def search_youtube(self,words,sentence,passed_url):
        if all(x in str(sentence).lower().split() and x is not None for x in words ):
            new_sentence = str(sentence)
            for x in words:
                new_sentence=str(new_sentence).replace(x,"").strip()
            youtube_url = "{}results?search_query={}".format(
                passed_url,
                quote_plus(new_sentence),
            )
            self.open_url(youtube_url)
           
    
    def search_google(self,words,sentence,passed_url):
        if all(x in str(sentence).lower().split() and x is not None for x in words):
            new_sentence = str(sentence)
            for x in words:
                new_sentence=str(new_sentence).replace(x,"").strip()
            google_url = "{}search?q={}".format(
                passed_url,
                quote_plus(new_sentence),
            )
            self.open_url(google_url)
            
    def search_giphy(self,words,sentence,passed_url):
        if all(x in str(sentence).lower().split() and x is not None for x in words):
            new_sentence = sentence
            for x in words:
                new_sentence=str(new_sentence).replace(x,"").strip()
            giphy_url = "{}search/{}".format(
                passed_url,
                quote_plus(new_sentence).replace("+", "-"),
            )
            self.open_url(giphy_url)

    def search_youtube_ini(self,passed_phrase):
        self.search_youtube(["search","youtube","for"],passed_phrase,self.youtube_url)

    # Google Search
    # words: list of words to identify the command
    # sentence: full user input
    # passed_url: base url to use for the search
    # Example: words = ["search","google","for"], sentence = "search google for cute cats", passed_url = "https://www.google.com/"
    # Look at the example above, if all words in the list are found in the sentence, the function will extract the search terms (cute cats) and open a new tab with the search results on Google.
    # Search google method is being called in the init function below.
    def search_google_ini(self,passed_phrase):
        self.search_google(["search","google","for"],passed_phrase,self.google_url)
    
    def search_giphy_ini(self,passed_phrase):
        self.search_giphy(["search","giphy","for"],passed_phrase,self.giphy_url)

    def use_workspace(self, user_input):
        workspace_name = str(user_input).removeprefix("use workspace").strip()
        if not workspace_name:
            return [self.return_status(False), self.message_handler("Add a workspace name.")]

        workspaces = list_workspaces()
        matches = [
            workspace
            for workspace in workspaces
            if workspace.get("id", "").lower() == workspace_name.lower()
            or workspace.get("name", "").lower() == workspace_name.lower()
        ]
        if not matches:
            available = ", ".join(workspace.get("name", "") for workspace in workspaces)
            suffix = f" Available workspaces: {available}." if available else ""
            return [
                self.return_status(False),
                self.message_handler(f"Workspace not found: {workspace_name}.{suffix}"),
            ]

        workspace = matches[0]
        try:
            settings = json.loads(APP_SETTINGS_FILE.read_text(encoding="utf-8"))
            if not isinstance(settings, dict):
                settings = {}
        except (OSError, json.JSONDecodeError):
            settings = {}

        settings["active_workspace"] = workspace["id"]
        temporary_file = APP_SETTINGS_FILE.with_suffix(".json.tmp")
        temporary_file.write_text(json.dumps(settings, indent=2), encoding="utf-8")
        temporary_file.replace(APP_SETTINGS_FILE)
        return [
            self.return_status(True),
            self.message_handler(f"Active workspace set to {workspace['name']}."),
        ]

    def select_tool(self, user_input):
        match user_input:
            case "open browser":
                self.open_browser()
                return [self.return_status(True),self.message_handler("Opening web browser !")]
            case _ if str(user_input).lower().startswith("use workspace "):
                return self.use_workspace(user_input)
            case _ if all(x in str(user_input).lower().split() and x is not None for x in ["search","youtube","for"]):
                self.search_youtube_ini(user_input)
                return [self.return_status(True),self.message_handler("Searching Youtube for {}!".format(str(user_input).replace("search youtube for","").strip()))]
            case _ if all(x in str(user_input).lower().split() and x is not None for x in ["search","google","for"]):
                self.search_google_ini(user_input)
                return [self.return_status(True),self.message_handler("Searching Google for {}!".format(str(user_input).replace("search google for","").strip()))]
            case _ if all(x in str(user_input).lower().split() and x is not None for x in ["search","giphy","for"]):
                self.search_giphy_ini(user_input)
                return [self.return_status(True),self.message_handler("Searching Giphy for {}!".format(str(user_input).replace("search giphy for","").strip()))]
            case _:
                return [self.return_status(False),self.message_handler(None)]
