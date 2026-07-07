# Cordada 🏔️

Plataforma web para la creación de comunidad y organización de actividades de montaña.

Trabajo de Fin de Grado — Ingeniería Informática.

## ¿Qué es Cordada?

Una plataforma sencilla y gratuita donde cualquier aficionado a la montaña puede:

- Crear un perfil y formar parte de la comunidad.
- Publicar actividades (rutas, ascensiones, travesías...).
- Apuntarse a actividades de otros usuarios.
- Compartir el recorrido mediante un archivo GPX visualizado sobre un mapa.
- Buscar y filtrar actividades por dificultad y fecha.

## Stack tecnológico

| Componente | Tecnología | Motivo |
|---|---|---|
| Backend | Django 5.2 LTS (Python) | Framework maduro, "baterías incluidas": autenticación, ORM, CSRF, admin |
| Frontend | Plantillas Django + Bootstrap 5 | Sin SPA; simplicidad y diseño responsive |
| Base de datos | SQLite (desarrollo) / PostgreSQL (producción) | Cero configuración en local; robustez en despliegue |
| Mapas | Leaflet + OpenStreetMap | Gratuito y sin claves de API |
| Despliegue | Render (plan gratuito) | Requisito del proyecto |

## Puesta en marcha en local

```bash
# 1. Clonar el repositorio
git clone https://github.com/antonio-gallego-ortiz/Cordada.git
cd Cordada

# 2. Crear y activar el entorno virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Aplicar migraciones
python manage.py migrate

# 5. Arrancar el servidor de desarrollo
python manage.py runserver
```

La aplicación quedará disponible en `http://127.0.0.1:8000/`.

## Tests

```bash
python manage.py test
```

## Estructura del proyecto

- `cordada/` — configuración del proyecto Django.
- `accounts/` — gestión de usuarios: registro, perfil, autenticación.
- `activities/` — actividades, inscripciones y tracks GPX.
- `templates/` — plantillas HTML compartidas.
