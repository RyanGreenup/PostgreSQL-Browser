#!/usr/bin/env python3
import sys
import signal
from PySide6.QtWidgets import QApplication
import typer
from typing import Optional

from data_types import ConnectionConfig

from main_window_new import MainWindow

app = typer.Typer()


@app.command()
def postgres(
    host: str = typer.Option("localhost", help="Database host"),
    port: int = typer.Option(5432, help="Database port"),
    username: str = typer.Option("postgres", help="Database username"),
    password: Optional[str] = typer.Option(
        None, help="Database password", prompt=True, hide_input=True
    ),
    openai_url: str = typer.Option("http://localhost:11434", help="OpenAI API URL"),
) -> None:
    qt_app = QApplication(sys.argv)
    conf = ConnectionConfig(host, port, username, password, openai_url)
    main_window = MainWindow(conf)
    main_window.show()
    sys.exit(qt_app.exec())


@app.command()
def sqlite():
    raise NotImplementedError("SQLite support is not yet implemented")


@app.command()
def mysql():
    raise NotImplementedError("MySQL support is not yet implemented")


@app.command()
def mariadb():
    raise NotImplementedError("MariaDB support is not yet implemented")


@app.command()
def oracle():
    raise NotImplementedError("Oracle support is not yet implemented")


@app.command()
def mssql():
    raise NotImplementedError("MSSQL support is not yet implemented")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app()
