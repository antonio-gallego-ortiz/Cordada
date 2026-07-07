from django.shortcuts import render


def activity_list(request):
    """Listado de actividades (portada). Se completará con el modelo Activity."""
    return render(request, "activities/activity_list.html")
