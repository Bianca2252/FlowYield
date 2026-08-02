"""FlowYield development entry point."""

import os
import webbrowser
from threading import Timer

from app import create_app

app = create_app()


def open_browser() -> None:
    """Open the local FlowYield application in the default browser."""
    webbrowser.open_new("http://127.0.0.1:5000")


if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        Timer(1.0, open_browser).start()

    app.run(debug=True)
