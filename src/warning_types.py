import warnings
import traceback
from typing import Optional


# Define custom warning classes
class DatabaseWarning(Warning):
    """Base class for database-related warnings."""


class ConnectionWarning(DatabaseWarning):
    """Specific warning for database connection issues."""


class QueryWarning(DatabaseWarning):
    """Specific warning for executing queries."""


class TableWarning(DatabaseWarning):
    """Specific warning for table-related operations."""


class GUIWarning(Warning):
    """Warnings related to the GUI"""


class TreeWarning(GUIWarning):
    """Warnings about Drawing Tree Elements"""


# Utility function to issue warnings
def issue_warning(
    message: str, warning_class=Warning, exception: Optional[Exception] = None
) -> None:
    """
    Centralized function to issue warnings in a standardized manner.

    :param message: The warning message to issue.
    :param warning_class: The class of warning to raise, defaults to DatabaseWarning.
    :param exception: The optional exception to include in the warning message.
    """
    # Add traceback information
    traceback_info = traceback.format_exc() if exception else ""
    full_message = f"{message}\n{traceback_info}".strip()  # Add traceback if available
    warnings.warn(full_message, warning_class, stacklevel=2)


def unable_to_connect_to_database(exception: Optional[Exception] = None) -> None:
    """
    Issue a warning for being unable to connect to a database.
    """
    issue_warning(
        f"Unable to connect to the database. {exception}", ConnectionWarning, exception
    )
