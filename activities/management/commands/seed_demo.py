"""Comando de datos de ejemplo para desarrollo y demostraciones.

Uso: python manage.py seed_demo

Crea usuarios con deportes, actividades reales españolas con datos
técnicos, tracks GPX aproximados y conversaciones de ejemplo.
Es idempotente: si los datos ya existen no hace nada.
"""

from datetime import timedelta
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageColor, ImageDraw, ImageFont

from accounts.models import UserSport
from activities.models import Activity, ActivityMessage, ActivityPhoto, register_user_for_activity
from communities.models import Community, CommunityMessage, Membership
from feed.models import Follow, Post, PostComment, PostImage, PostLike
from market.models import Conversation, Listing, ListingImage, MarketMessage

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


LISTINGS = [
    {
        "title": "Botas La Sportiva Trango Tower (42)",
        "description": (
            "Botas de alta montaña semirrígidas, cramponables. Dos temporadas de uso, "
            "suela en muy buen estado. Las vendo por cambio de talla."
        ),
        "category": "footwear",
        "condition": "good",
        "offer_type": "sale",
        "price": "95.00",
        "location": "Granada",
        "seller": "demo",
    },
    {
        "title": "Esquís de travesía + pieles (170 cm)",
        "description": (
            "Equipo completo de travesía: esquís con fijaciones y pieles a medida. "
            "Ideal para iniciarse sin gastarse un dineral. Alquiler por días o fines de semana."
        ),
        "category": "snow",
        "condition": "good",
        "offer_type": "rent",
        "price": "18.00",
        "location": "Granada",
        "seller": "luis",
    },
    {
        "title": "Cuerda dinámica 60 m (revisar antes de usar)",
        "description": (
            "Cuerda de escalada de 9,8 mm y 60 m. Sin caídas fuertes, guardada en seco. "
            "La presto gratis a gente del club para salidas puntuales."
        ),
        "category": "climbing",
        "condition": "used",
        "offer_type": "loan",
        "price": None,
        "location": "Monachil",
        "seller": "ana",
    },
    {
        "title": "Tienda MSR Hubba Hubba 2 plazas",
        "description": (
            "Tienda ligera de 3 estaciones, 1,7 kg. Usada en dos travesías, sin roturas "
            "ni reparaciones. Incluye footprint."
        ),
        "category": "camping",
        "condition": "like_new",
        "offer_type": "sale",
        "price": "260.00",
        "location": "Madrid",
        "seller": "marta",
    },
    {
        "title": "GPS Garmin eTrex 32x",
        "description": "GPS de mano con mapas topográficos de España cargados. Con funda y cable.",
        "category": "electronics",
        "condition": "like_new",
        "offer_type": "sale",
        "price": "140.00",
        "location": "León",
        "seller": "luis",
    },
]


POSTS = [
    {
        "author": "ana",
        "content": (
            "¡Por fin cayó la Espolón de la Virgen en el Chorro! 6a+ de placer, "
            "roca impecable y cero colas a primera hora. Si alguien se anima a "
            "repetirla este mes, que me escriba: se me ha quedado corta."
        ),
        "likes": ["demo", "luis", "marta"],
        "comments": [
            ("luis", "¡Enhorabuena! Ese espolón es una gozada."),
            ("marta", "Algún día me llevas, ¿no? 😅"),
        ],
    },
    {
        "author": "demo",
        "content": (
            "Resumen del finde: Vereda de la Estrella con un grupo de 8, tiempo "
            "perfecto y los primeros neveros a la vista. Gracias a todos los que "
            "vinisteis, ¡repetimos en dos semanas con la ruta de los refugios!"
        ),
        "likes": ["ana", "marta"],
        "comments": [
            ("marta", "Me lo pasé genial, ¡gracias por organizar!"),
        ],
    },
    {
        "author": "luis",
        "content": (
            "Ojo con la loma del Veleta este fin de semana: el parte da viento "
            "fuerte en cotas altas y la nieve está muy transformada. Si vais con "
            "esquís, mejor por la vertiente sur y pronto."
        ),
        "likes": ["demo"],
        "comments": [],
    },
    {
        "author": "marta",
        "content": (
            "Primera ruta con crampones ayer en los Cahorros altos. Todavía me "
            "tiemblan las piernas pero QUÉ PASADA. Gracias Ana por la paciencia "
            "infinita. Siguiente objetivo: un tresmil en condiciones."
        ),
        "likes": ["ana", "demo", "luis"],
        "comments": [
            ("ana", "¡Lo hiciste genial! El Mulhacén te espera."),
            ("demo", "Así se empieza. 💪"),
        ],
    },
]

FOLLOWS = [
    ("marta", "ana"),
    ("marta", "demo"),
    ("marta", "luis"),
    ("ana", "demo"),
    ("demo", "ana"),
    ("luis", "ana"),
]

COMMUNITIES = [
    {
        "name": "Montañeros de Granada",
        "description": (
            "Grupo abierto para organizar salidas por Sierra Nevada y alrededores. "
            "Todos los niveles bienvenidos."
        ),
        "creator": "demo",
        "members": ["ana", "luis", "marta"],
        "chat": [
            ("demo", "¡Bienvenidos al grupo! Id presentándoos por aquí."),
            ("marta", "¡Hola! Soy Marta, empezando en esto pero con muchas ganas."),
            ("luis", "Yo suelo subir entre semana si alguien se anima."),
        ],
    },
    {
        "name": "Escaladores de Madrid",
        "description": (
            "Quedadas de escalada en La Pedriza, Patones y rocódromos de la capital."
        ),
        "creator": "ana",
        "members": ["marta"],
        "chat": [
            ("ana", "¿Alguien para Patones este sábado? Busco pareja de cordada."),
        ],
    },
    {
        "name": "Esquí de travesía peninsular",
        "description": (
            "Partes de nieve, tracks y compañeros de travesía por todas las "
            "cordilleras de la península."
        ),
        "creator": "luis",
        "members": ["demo"],
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


def make_demo_image(text_lines, bg_color, accent_color, accent2, filename):
    """Crea una imagen PNG sencilla con estilo de montaña para la demo."""
    width, height = 1200, 900
    bg = ImageColor.getrgb(bg_color) if isinstance(bg_color, str) else bg_color
    accent = ImageColor.getrgb(accent_color) if isinstance(accent_color, str) else accent_color
    accent_b = ImageColor.getrgb(accent2) if isinstance(accent2, str) else accent2
    image = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(image)

    for y in range(height):
        ratio = y / height
        r = int((1 - ratio) * 255 + ratio * accent[0])
        g = int((1 - ratio) * 255 + ratio * accent[1])
        b = int((1 - ratio) * 255 + ratio * accent[2])
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    draw.polygon(
        [(0, 680), (180, 480), (360, 640), (560, 420), (780, 680), (980, 500), (1200, 620), (1200, 900), (0, 900)],
        fill=accent,
    )
    draw.polygon(
        [(0, 900), (220, 760), (420, 840), (640, 700), (840, 820), (1200, 740), (1200, 900)],
        fill=accent_b,
    )
    draw.ellipse((900, 70, 1120, 290), fill=(255, 255, 255))
    draw.rounded_rectangle((70, 90, 1120, 180), radius=34, fill=(255, 255, 255))
    draw.rounded_rectangle((70, 220, 780, 320), radius=24, fill=(255, 255, 255))

    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 54)
        font_body = ImageFont.truetype("DejaVuSans.ttf", 32)
    except OSError:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()

    draw.multiline_text((90, 120), "\n".join(text_lines[:2]), fill="white", font=font_title)
    if len(text_lines) > 2:
        draw.text((90, 240), text_lines[2], fill=(240, 250, 244), font=font_body)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=filename)


def make_avatar_image(initial, filename):
    """Crea una imagen de avatar con tono verde y una letra inicial."""
    image = Image.new("RGB", (512, 512), "#f5f7f6")
    draw = ImageDraw.Draw(image)
    draw.ellipse((16, 16, 496, 496), fill="#059669")
    draw.ellipse((40, 40, 472, 472), fill="#10b981")
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 220)
    except OSError:
        font = ImageFont.load_default()
    draw.text((256, 256), initial.upper(), fill="white", font=font, anchor="mm")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=filename)


class Command(BaseCommand):
    help = "Crea datos de ejemplo (usuarios, actividades con GPX y chats)."

    def handle(self, *args, **options):
        users = {}
        for data in USERS:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "email": f"{data['username']}@example.com",
                    "password": PASSWORD,
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "bio": data["bio"],
                },
            )
            if created:
                user.set_password(PASSWORD)
                user.save(update_fields=["password"])
            else:
                user.first_name = data["first_name"]
                user.last_name = data["last_name"]
                user.bio = data["bio"]
                user.email = f"{data['username']}@example.com"
                user.save(update_fields=["first_name", "last_name", "bio", "email"])

            if not user.photo:
                self.ensure_user_photo(user, data["first_name"] or data["username"])

            for sport, level in data["sports"].items():
                UserSport.objects.get_or_create(user=user, sport=sport, defaults={"level": level})
                if not UserSport.objects.filter(user=user, sport=sport).exists():
                    UserSport.objects.filter(user=user, sport=sport).update(level=level)
            users[data["username"]] = user

        for data in ACTIVITIES:
            activity, created = Activity.objects.get_or_create(
                title=data["title"],
                defaults={
                    "description": data["description"],
                    "date": timezone.now() + timedelta(days=data["days"]),
                    "difficulty": data["difficulty"],
                    "location": data["location"],
                    "meeting_point": data["meeting_point"],
                    "max_participants": data["max_participants"],
                    "organizer": users[data["organizer"]],
                    "distance_km": data["distance_km"],
                    "elevation_gain_m": data["elevation_gain_m"],
                    "duration_hours": data["duration_hours"],
                    "equipment": data["equipment"],
                    "latitude": data["waypoints"][0][0],
                    "longitude": data["waypoints"][0][1],
                },
            )
            if activity.latitude is None:
                activity.latitude, activity.longitude = data["waypoints"][0]
                activity.save(update_fields=["latitude", "longitude"])
            if created:
                gpx_content = build_gpx(data["title"], data["waypoints"])
                filename = data["title"].lower().replace(" ", "_").replace(":", "")[:40]
                activity.gpx_file.save(
                    f"{filename}.gpx", ContentFile(gpx_content.encode()), save=True
                )
            elif not activity.gpx_file:
                gpx_content = build_gpx(data["title"], data["waypoints"])
                filename = data["title"].lower().replace(" ", "_").replace(":", "")[:40]
                activity.gpx_file.save(
                    f"{filename}.gpx", ContentFile(gpx_content.encode()), save=True
                )

            if not activity.photos.exists():
                self.ensure_activity_photo(activity, data["title"])

            for username in data["participants"]:
                if not activity.registrations.filter(user=users[username]).exists():
                    register_user_for_activity(users[username], activity.pk)
            for username, content in data["chat"]:
                if not activity.messages.filter(user=users[username], content=content).exists():
                    ActivityMessage.objects.create(
                        activity=activity, user=users[username], content=content
                    )

        self.seed_listings(users)
        self.seed_social(users)

        self.stdout.write(
            self.style.SUCCESS(
                f"Datos de demo creados: {len(USERS)} usuarios, "
                f"{len(ACTIVITIES)} actividades, {len(LISTINGS)} anuncios, "
                f"{len(POSTS)} publicaciones y {len(COMMUNITIES)} comunidades "
                f"(contraseña: {PASSWORD})."
            )
        )

    def ensure_user_photo(self, user, label):
        if user.photo:
            return
        filename = f"{user.username}_avatar.png"
        image = make_avatar_image(label[:1], filename)
        user.photo.save(filename, image, save=True)

    def ensure_activity_photo(self, activity, title):
        if activity.photos.exists():
            return
        filename = f"{activity.pk}_{title.lower().replace(' ', '_')}.png"
        image = make_demo_image(
            [title, "Ruta de montaña", "Una experiencia de demo para mostrar la interfaz."],
            "#f4f6f5",
            "#059669",
            "#0f766e",
            filename,
        )
        ActivityPhoto.objects.create(activity=activity, image=image)

    def seed_listings(self, users):
        """Crea los anuncios del mercado y una conversación de ejemplo."""
        listings = {}
        for data in LISTINGS:
            listing, created = Listing.objects.get_or_create(
                title=data["title"],
                defaults={
                    "description": data["description"],
                    "category": data["category"],
                    "condition": data["condition"],
                    "offer_type": data["offer_type"],
                    "price": data["price"],
                    "location": data["location"],
                    "seller": users[data["seller"]],
                },
            )
            if not listing.images.exists():
                filename = f"{listing.title.lower().replace(' ', '_').replace('(', '').replace(')', '')[:40]}.png"
                image = make_demo_image(
                    [listing.title, listing.get_offer_type_display(), listing.location],
                    "#f8fafc",
                    "#047857",
                    "#0f766e",
                    filename,
                )
                listing_image = ListingImage(listing=listing)
                listing_image.image.save(filename, image, save=True)
            listings[data["title"]] = listing

        boots = listings["Botas La Sportiva Trango Tower (42)"]
        conversation, _ = Conversation.objects.get_or_create(
            listing=boots, buyer=users["marta"]
        )
        if not conversation.messages.exists():
            MarketMessage.objects.create(
                conversation=conversation,
                sender=users["marta"],
                content="¡Hola! ¿Las botas siguen disponibles? ¿Aceptarías 85 €?",
            )
            MarketMessage.objects.create(
                conversation=conversation,
                sender=users["demo"],
                content="Hola Marta, sí. Por 90 € te las llevo yo a la próxima quedada.",
            )

    def seed_social(self, users):
        """Crea publicaciones, seguimientos y comunidades de ejemplo."""
        for data in POSTS:
            post, created = Post.objects.get_or_create(
                author=users[data["author"]],
                content=data["content"],
            )
            # La primera publicación lleva varias imágenes para lucir el
            # carrusel en la demo; el resto, una. Se completan las que falten.
            variants = [("#f8fafc", "#059669", "#064e3b")]
            if data is POSTS[0]:
                variants += [
                    ("#eff6ff", "#2563eb", "#1e3a8a"),
                    ("#fff7ed", "#ea580c", "#7c2d12"),
                ]
            existing = post.images.count()
            for index, (bg, accent, accent2) in enumerate(
                variants[existing:], start=existing
            ):
                filename = f"{post.author.username}_{post.pk or 'post'}_{index}.png"
                image = make_demo_image(
                    ["Cordada", "Feed social", data["content"][:80]],
                    bg,
                    accent,
                    accent2,
                    filename,
                )
                post_image = PostImage(post=post)
                post_image.image.save(filename, image, save=True)
            for username in data["likes"]:
                PostLike.objects.get_or_create(post=post, user=users[username])
            for username, content in data["comments"]:
                PostComment.objects.get_or_create(
                    post=post,
                    author=users[username],
                    content=content,
                )

        for follower, followed in FOLLOWS:
            Follow.objects.get_or_create(
                follower=users[follower], followed=users[followed]
            )

        for data in COMMUNITIES:
            community, _ = Community.objects.get_or_create(
                name=data["name"],
                defaults={
                    "description": data["description"],
                    "created_by": users[data["creator"]],
                },
            )
            if not community.memberships.filter(user=users[data["creator"]]).exists():
                Membership.objects.create(community=community, user=users[data["creator"]])
            for username in data["members"]:
                if not community.memberships.filter(user=users[username]).exists():
                    Membership.objects.create(community=community, user=users[username])
            for username, content in data["chat"]:
                if not community.messages.filter(sender=users[username], content=content).exists():
                    CommunityMessage.objects.create(
                        community=community, sender=users[username], content=content
                    )
