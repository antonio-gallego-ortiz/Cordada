from django.core.exceptions import ValidationError

MAX_UPLOAD_MB = 5


def validate_upload_size(uploaded_file):
    """Limita el tamaño de los archivos subidos por los usuarios."""
    if uploaded_file.size > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValidationError(
            f"El archivo no puede superar los {MAX_UPLOAD_MB} MB."
        )
