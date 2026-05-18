import csv
import io
from datetime import timezone

from app.src.models.todo import TodoItem


class CsvExportService:
    """Service for converting TodoItem instances to RFC 4180-compliant CSV."""

    COLUMNS = ["id", "title", "description", "completed", "created_at"]

    @staticmethod
    def generate(items: list[TodoItem]) -> str:
        """Convert a list of TodoItem objects to an RFC 4180 CSV string.

        Returns UTF-8 encoded string without BOM, using CRLF line endings
        and csv.QUOTE_MINIMAL quoting strategy.
        """
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")

        # Write header row
        writer.writerow(CsvExportService.COLUMNS)

        # Write data rows
        for item in items:
            # Format created_at as ISO 8601 with "Z" suffix
            # Replace +00:00 timezone with Z for UTC designator
            dt = item.created_at
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            created_at_str = dt.isoformat() + "Z"

            row = [
                str(item.id),
                item.title,
                item.description if item.description is not None else "",
                "true" if item.completed else "false",
                created_at_str,
            ]
            writer.writerow(row)

        return output.getvalue()
