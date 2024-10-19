check:
    pyright src/*.py
    vulture src/*.py
    ruff check
    ruff format
    pytype syrc/main.py

lw:
    poetry run python src/main.py postgres  --host localhost --password adslkjflkje --username postgres --port 37194
run:
    poetry run python src/main.py postgres  --host localhost --password postgres --username postgres --port 5432

install:
    pipx install . --force

install_remote:
    pipx install "git+https://github.com/RyanGreenup/PostgreSQL-Browser" --force
