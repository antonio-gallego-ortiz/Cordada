from django.core.paginator import Paginator


def paginate(request, object_list, per_page):
    """Pagina un listado conservando el resto de parámetros de la URL.

    Devuelve la página actual y la cadena de consulta (sin ``page``)
    para construir los enlaces de paginación en la plantilla.
    """
    paginator = Paginator(object_list, per_page)
    page_obj = paginator.get_page(request.GET.get("page"))
    # Rango con elipsis (1 … 4 5 6 … 12) listo para usar en la plantilla.
    page_obj.elided_range = paginator.get_elided_page_range(
        page_obj.number, on_each_side=2, on_ends=1
    )
    params = request.GET.copy()
    params.pop("page", None)
    return page_obj, params.urlencode()
