#!/usr/bin/env python3
import sys
import signal
from PyQt6.QtWidgets import QApplication
import typer
from typing import Optional

from main_window import MainWindow

app = typer.Typer()


@app.command()
def main(
    host: str = typer.Option("localhost", help="Database host"),
    port: int = typer.Option(5432, help="Database port"),
    username: str = typer.Option("postgres", help="Database username"),
    password: Optional[str] = typer.Option(
        None, help="Database password", prompt=True, hide_input=True
    ),
    openai_url: str = typer.Option("http://localhost:11434", help="OpenAI API URL"),
) -> None:
    qt_app = QApplication(sys.argv)
    main_window = MainWindow(host, port, username, password, openai_url)
    main_window.show()
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app()
