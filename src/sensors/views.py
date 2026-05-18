from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services import get_latest_records, get_record_summary


@login_required
def import_status(request):
    summary = get_record_summary()
    latest_records = get_latest_records()
    return render(
        request,
        "sensors/import_status.html",
        {
            "summary": summary,
            "latest_records": latest_records,
            "csv_path": "data/processed/enviropro_completo_2024_2026.csv",
            "import_command": "python manage.py import_enviropro",
        },
    )
