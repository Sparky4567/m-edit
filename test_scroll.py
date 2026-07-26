from textual.app import App, ComposeResult
from textual.widgets import Markdown
import asyncio

class TestApp(App):
    CSS = """
    Markdown {
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
    }
    """
    def compose(self) -> ComposeResult:
        yield Markdown("# Test\n\n" + "line\n\n" * 100)
    def on_mount(self) -> None:
        asyncio.get_running_loop().call_later(1, self.exit)

if __name__ == "__main__":
    TestApp().run()
