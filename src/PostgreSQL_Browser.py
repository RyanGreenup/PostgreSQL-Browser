#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import QApplication
import typer
from typing import Optional, Any

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
) -> None:
    qt_app = QApplication(sys.argv)
    main_window = MainWindow(host, port, username, password)
    main_window.show()
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    app()
