from django.db import connection
from django.http import JsonResponse


def health(request):
    """Comprobación de salud para el despliegue: proceso vivo y base de datos accesible."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ok"})
