"""Comando de datos de ejemplo para desarrollo y demostraciones.

Uso: python manage.py seed_demo

Crea usuarios con deportes, actividades reales españolas con datos
técnicos, tracks GPX aproximados y conversaciones de ejemplo.
Es idempotente: si los datos ya existen no hace nada.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import UserSport
from activities.models import Activity, ActivityMessage, register_user_for_activity

User = get_user_model()

PASSWORD = "demo-cordada-2026"

USERS = [
    {
        "username": "demo",
        "first_name": "Demo",
        "last_name": "Cordada",
        "bio": "Cuenta de demostración. Me encanta la alta montaña y el café del refugio.",
        "sports": {"hiking": "advanced", "mountaineering": "intermediate", "skiing": "beginner"},
    },
    {
        "username": "ana",
        "first_name": "Ana",
        "last_name": "Serrano",
        "bio": "Escaladora de fin de semana y coleccionista de amaneceres.",
        "sports": {"climbing": "advanced", "hiking": "expert"},
    },
    {
        "username": "luis",
        "first_name": "Luis",
        "last_name": "Ortega",
        "bio": "Esquiador de travesía. En verano, trail y barrancos.",
        "sports": {"skiing": "expert", "trail_running": "intermediate", "canyoning": "advanced"},
    },
    {
        "username": "marta",
        "first_name": "Marta",
        "last_name": "Vidal",
        "bio": "Empezando en esto de la montaña, ¡con muchas ganas de aprender!",
        "sports": {"hiking": "beginner", "snowboarding": "intermediate"},
    },
]

# Cada track se genera interpolando entre puntos de paso aproximados
# (suficiente para la demostración del mapa).
ACTIVITIES = [
    {
        "title": "Vereda de la Estrella",
        "description": (
            "Ruta clásica de Sierra Nevada remontando el valle del Genil, "
            "con las mejores vistas de la cara norte del Mulhacén y la Alcazaba. "
            "Ritmo tranquilo con paradas para fotos; comeremos junto al Real."
        ),
        "days": 9,
        "difficulty": "moderate",
        "location": "Sierra Nevada, Granada",
        "meeting_point": "Barranco de San Juan (Güéjar Sierra)",
        "max_participants": 8,
        "organizer": "demo",
        "distance_km": "18.5",
        "elevation_gain_m": 750,
        "duration_hours": "6.5",
        "equipment": "Botas de montaña, 2 L de agua, comida, cortavientos y gorra. Bastones recomendados.",
        "waypoints": [(37.1583, -3.3266), (37.1490, -3.3110), (37.1408, -3.2965), (37.1315, -3.2820)],
        "participants": ["ana", "marta"],
        "chat": [
            ("ana", "¿A qué hora llegamos al Barranco de San Juan? ¿Compartimos coches?"),
            ("demo", "Yo salgo de Granada a las 7:30, tengo 3 plazas libres."),
            ("marta", "¡Me apunto al coche! Llevo bizcocho para el descanso."),
        ],
    },
    {
        "title": "Subida al Veleta desde la Hoya de la Mora",
        "description": (
            "Ascensión al tercer pico de la península (3.396 m) por las Posiciones "
            "del Veleta. Exigente por la altitud, sin dificultad técnica en verano."
        ),
        "days": 16,
        "difficulty": "hard",
        "location": "Sierra Nevada, Granada",
        "meeting_point": "Aparcamiento Hoya de la Mora",
        "max_participants": 6,
        "organizer": "ana",
        "distance_km": "14.0",
        "elevation_gain_m": 900,
        "duration_hours": "7.0",
        "equipment": "Botas, 2,5 L de agua, protección solar alta, cortavientos, gorro y guantes (arriba refresca incluso en verano).",
        "waypoints": [(37.0956, -3.3866), (37.0862, -3.3776), (37.0700, -3.3689), (37.0563, -3.3653)],
        "participants": ["demo", "luis"],
        "chat": [
            ("luis", "¿Hará falta piolet a estas alturas del año?"),
            ("ana", "No, el nevero de las Posiciones ya está pasable. Bastones y listo."),
        ],
    },
    {
        "title": "Los Cahorros de Monachil",
        "description": (
            "Paseo por los desfiladeros y puentes colgantes del río Monachil. "
            "Perfecta para iniciarse y conocer gente: acabaremos con unas tapas en el pueblo."
        ),
        "days": 4,
        "difficulty": "easy",
        "location": "Monachil, Granada",
        "meeting_point": "Plaza Baja de Monachil",
        "max_participants": 15,
        "organizer": "marta",
        "distance_km": "8.0",
        "elevation_gain_m": 250,
        "duration_hours": "3.5",
        "equipment": "Zapatillas de trekking, 1 L de agua y algo de picar.",
        "waypoints": [(37.1310, -3.5370), (37.1289, -3.5237), (37.1256, -3.5105), (37.1290, -3.5320)],
        "participants": ["demo", "ana", "luis"],
        "chat": [
            ("demo", "¿La ruta es apta para llevar a mi primo de 12 años?"),
            ("marta", "¡Sí! Los puentes colgantes le van a encantar."),
        ],
    },
    {
        "title": "Ruta del Cares: Poncebos - Caín",
        "description": (
            "La Garganta Divina de los Picos de Europa. Sendero espectacular tallado "
            "en la roca sobre el desfiladero del Cares. Ida y vuelta con parada en Caín."
        ),
        "days": 30,
        "difficulty": "moderate",
        "location": "Picos de Europa, Asturias/León",
        "meeting_point": "Aparcamiento de Poncebos",
        "max_participants": 10,
        "organizer": "luis",
        "distance_km": "22.0",
        "elevation_gain_m": 500,
        "duration_hours": "7.0",
        "equipment": "Calzado de trekking, agua abundante (no hay fuentes fiables en el tramo central), gorra y crema solar.",
        "waypoints": [(43.2565, -4.8253), (43.2430, -4.8395), (43.2237, -4.8506), (43.2043, -4.8886)],
        "participants": ["ana"],
        "chat": [],
    },
    {
        "title": "Esquí de travesía: Loma del Mulhacén",
        "description": (
            "Salida de esquí de travesía por la loma del Mulhacén desde la Hoya del Portillo. "
            "Solo para gente con experiencia previa y material completo de seguridad."
        ),
        "days": 45,
        "difficulty": "very_hard",
        "location": "Sierra Nevada, Granada",
        "meeting_point": "Hoya del Portillo (Capileira)",
        "max_participants": 5,
        "organizer": "luis",
        "distance_km": "16.0",
        "elevation_gain_m": 1250,
        "duration_hours": "8.0",
        "equipment": "Esquís de travesía con pieles, ARVA, pala y sonda obligatorios. Crampones y piolet. Ropa de alta montaña invernal.",
        "waypoints": [(36.9962, -3.3634), (37.0203, -3.3486), (37.0410, -3.3170), (37.0530, -3.3110)],
        "participants": [],
        "chat": [],
    },
]


def build_gpx(name, waypoints, points_per_leg=12):
    """Genera un GPX sencillo interpolando entre puntos de paso."""
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gpx version="1.1" creator="cordada-seed" '
        'xmlns="http://www.topografix.com/GPX/1/1">',
        f"<trk><name>{name}</name><trkseg>",
    ]
    elevation = 1100
    for (lat1, lon1), (lat2, lon2) in zip(waypoints, waypoints[1:]):
        for step in range(points_per_leg):
            fraction = step / points_per_leg
            lat = lat1 + (lat2 - lat1) * fraction
            lon = lon1 + (lon2 - lon1) * fraction
            elevation += 18
            parts.append(
                f'<trkpt lat="{lat:.5f}" lon="{lon:.5f}"><ele>{elevation}</ele></trkpt>'
            )
    parts.append("</trkseg></trk></gpx>")
    return "\n".join(parts)


class Command(BaseCommand):
    help = "Crea datos de ejemplo (usuarios, actividades con GPX y chats)."

    def handle(self, *args, **options):
        if User.objects.filter(username="demo").exists():
            self.stdout.write(self.style.WARNING("Los datos de demo ya existen."))
            return

        users = {}
        for data in USERS:
            user = User.objects.create_user(
                username=data["username"],
                email=f"{data['username']}@example.com",
                password=PASSWORD,
                first_name=data["first_name"],
                last_name=data["last_name"],
                bio=data["bio"],
            )
            for sport, level in data["sports"].items():
                UserSport.objects.create(user=user, sport=sport, level=level)
            users[data["username"]] = user

        for data in ACTIVITIES:
            activity = Activity(
                title=data["title"],
                description=data["description"],
                date=timezone.now() + timedelta(days=data["days"]),
                difficulty=data["difficulty"],
                location=data["location"],
                meeting_point=data["meeting_point"],
                max_participants=data["max_participants"],
                organizer=users[data["organizer"]],
                distance_km=data["distance_km"],
                elevation_gain_m=data["elevation_gain_m"],
                duration_hours=data["duration_hours"],
                equipment=data["equipment"],
            )
            gpx_content = build_gpx(data["title"], data["waypoints"])
            filename = data["title"].lower().replace(" ", "_").replace(":", "")[:40]
            activity.gpx_file.save(
                f"{filename}.gpx", ContentFile(gpx_content.encode()), save=True
            )
            for username in data["participants"]:
                register_user_for_activity(users[username], activity.pk)
            for username, content in data["chat"]:
                ActivityMessage.objects.create(
                    activity=activity, user=users[username], content=content
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Datos de demo creados: {len(USERS)} usuarios y "
                f"{len(ACTIVITIES)} actividades (contraseña: {PASSWORD})."
            )
        )
