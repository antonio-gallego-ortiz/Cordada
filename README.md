# Cordada 🏔️

Plataforma web para la creación de comunidad y organización de actividades de montaña.

Trabajo de Fin de Grado — Ingeniería Informática.

## ¿Qué es Cordada?

Una plataforma sencilla y gratuita donde cualquier aficionado a la montaña puede:

- Compartir sus experiencias en el feed social: publicaciones con foto,
  me gusta, comentarios y seguimiento entre usuarios.
- Unirse a comunidades (Escaladores de Madrid, Montañeros de Granada...)
  con chat de grupo.
- Crear un perfil con sus deportes y nivel (senderismo, alpinismo, esquí, escalada...).
- Publicar actividades (rutas, ascensiones, travesías...) con datos técnicos
  (distancia, desnivel, duración) y el material necesario.
- Apuntarse a actividades de otros usuarios.
- Hablar con el resto de inscritos en el chat de cada actividad.
- Compartir el recorrido mediante un archivo GPX visualizado sobre un mapa.
- Buscar y filtrar actividades por dificultad y fecha.
- Comprar, vender, alquilar o prestar material de segunda mano en el mercado,
  con chat privado entre comprador y vendedor.

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

# 5. (Opcional) Cargar datos de ejemplo
python manage.py seed_demo

# 6. Arrancar el servidor de desarrollo
python manage.py runserver
```

La aplicación quedará disponible en `http://127.0.0.1:8000/`.

Los datos de ejemplo crean 4 usuarios (`demo`, `ana`, `luis`, `marta`,
contraseña `demo-cordada-2026`), 5 actividades con track GPX,
inscripciones y chats, 5 anuncios en el mercado, publicaciones en el
feed con me gusta y comentarios, seguimientos entre usuarios y
3 comunidades con conversaciones de grupo.

## Tests

```bash
python manage.py test
```

## Despliegue en Render

El repositorio incluye un blueprint ([render.yaml](render.yaml)) que crea el
servicio web y la base de datos PostgreSQL:

1. Entra en [Render](https://render.com) y elige **New → Blueprint**.
2. Conecta este repositorio: Render leerá `render.yaml` y creará el servicio
   `cordada` (plan gratuito) y la base de datos `cordada-db`.
3. El script [build.sh](build.sh) instala dependencias, recopila los
   estáticos y aplica las migraciones en cada despliegue.

Variables de entorno usadas en producción:

| Variable | Descripción |
|---|---|
| `SECRET_KEY` | Clave secreta de Django (Render la genera automáticamente) |
| `DEBUG` | `False` en producción |
| `DATABASE_URL` | Conexión a PostgreSQL (la inyecta Render desde la base de datos) |
| `ALLOWED_HOSTS` | Dominios extra separados por comas (opcional; el dominio de Render se añade solo) |
| `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL` | SMTP para los correos de recuperación de contraseña (por defecto, backend de consola) |
| `LOG_LEVEL` | Nivel de log (`INFO` por defecto) |

## Preparado para producción

- Recuperación de contraseña por email y cambio de contraseña desde el perfil.
- Páginas de error personalizadas (404, 403, 500) y endpoint de salud en `/salud/`.
- Paginación en el feed, las actividades y el mercado.
- Política de privacidad y términos de uso, con consentimiento en el registro (RGPD).
- Integración continua: los tests se ejecutan en GitHub Actions en cada push.
- Logging a consola configurable y favicon/robots.txt.

Futuras mejoras documentadas y fuera de alcance: limitación de intentos de
inicio de sesión (django-axes), monitorización de errores (Sentry) y
almacenamiento externo para los archivos subidos (S3/Cloudinary).

Para crear el usuario administrador en producción, desde la pestaña *Shell*
del servicio: `python manage.py createsuperuser`.

> **Limitación del plan gratuito:** el disco es efímero, así que los archivos
> subidos (fotos y GPX) se pierden en cada despliegue. Para conservarlos
> habría que usar un almacenamiento externo (S3, Cloudinary...), fuera del
> alcance de este proyecto.

## Estructura del proyecto

- `cordada/` — configuración del proyecto Django.
- `accounts/` — gestión de usuarios: registro, perfil, autenticación.
- `feed/` — feed social: publicaciones, me gusta, comentarios y seguimiento.
- `activities/` — actividades, inscripciones, tracks GPX y chat de actividad.
- `market/` — mercado de material de segunda mano con chat comprador-vendedor.
- `communities/` — comunidades y grupos con chat.
- `templates/` — plantillas HTML compartidas.
- `static/` — hoja de estilos y JavaScript propios.
