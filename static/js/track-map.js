/* Visor del track GPX con dos modos:
   - 2D: Leaflet con selector de capas (estándar, topográfico, satélite,
     relieve y ciclista), todas de proveedores gratuitos.
   - 3D: MapLibre GL con terreno real (tiles de elevación Terrarium de AWS,
     de acceso abierto) y el track dibujado sobre el relieve.
   MapLibre se carga bajo demanda la primera vez que se activa el 3D. */

function initCordadaTrackMap(options) {
    const map2dElement = document.getElementById(options.mapId || "map");
    const map3dElement = document.getElementById(options.map3dId || "map-3d");
    const button2d = document.getElementById(options.btn2dId || "btn-map-2d");
    const button3d = document.getElementById(options.btn3dId || "btn-map-3d");

    /* ---------- Modo 2D: Leaflet con capas ---------- */

    const baseLayers = {
        "Estándar": L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: "&copy; OpenStreetMap contributors"
        }),
        "Topográfico": L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
            maxZoom: 17,
            attribution: "&copy; OpenTopoMap (CC-BY-SA)"
        }),
        "Satélite": L.tileLayer(
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
            maxZoom: 19,
            attribution: "&copy; Esri &mdash; Maxar, Earthstar Geographics"
        }),
        "Relieve": L.tileLayer(
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}", {
            maxZoom: 13,
            attribution: "&copy; Esri"
        }),
        "Ciclista": L.tileLayer(
            "https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: "&copy; CyclOSM, OpenStreetMap contributors"
        })
    };

    const map = L.map(map2dElement, {layers: [baseLayers["Estándar"]]});
    L.control.layers(baseLayers).addTo(map);

    let trackBounds = null;
    new L.GPX(options.gpxUrl, {
        async: true,
        marker_options: {startIconUrl: null, endIconUrl: null, shadowUrl: null}
    }).on("loaded", function (event) {
        trackBounds = event.target.getBounds();
        map.fitBounds(trackBounds);
    }).addTo(map);

    /* ---------- Modo 3D: MapLibre con terreno ---------- */

    const MAPLIBRE_JS = "https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js";
    const MAPLIBRE_CSS = "https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css";
    let map3dReady = false;

    function loadMapLibre() {
        return new Promise(function (resolve, reject) {
            if (window.maplibregl) return resolve();
            const css = document.createElement("link");
            css.rel = "stylesheet";
            css.href = MAPLIBRE_CSS;
            document.head.appendChild(css);
            const script = document.createElement("script");
            script.src = MAPLIBRE_JS;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    function parseGpxCoordinates(gpxText) {
        const xml = new DOMParser().parseFromString(gpxText, "application/xml");
        const points = xml.querySelectorAll("trkpt, rtept, wpt");
        const coordinates = [];
        points.forEach(function (point) {
            coordinates.push([
                parseFloat(point.getAttribute("lon")),
                parseFloat(point.getAttribute("lat"))
            ]);
        });
        return coordinates;
    }

    function init3d() {
        Promise.all([loadMapLibre(), fetch(options.gpxUrl).then(r => r.text())])
            .then(function (results) {
                const coordinates = parseGpxCoordinates(results[1]);
                if (!coordinates.length) throw new Error("GPX sin puntos");

                const lons = coordinates.map(c => c[0]);
                const lats = coordinates.map(c => c[1]);
                const bounds = [
                    [Math.min.apply(null, lons), Math.min.apply(null, lats)],
                    [Math.max.apply(null, lons), Math.max.apply(null, lats)]
                ];

                const map3d = new maplibregl.Map({
                    container: map3dElement,
                    style: {
                        version: 8,
                        sources: {
                            satellite: {
                                type: "raster",
                                tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
                                tileSize: 256,
                                attribution: "© Esri — Maxar, Earthstar Geographics"
                            },
                            terrain: {
                                type: "raster-dem",
                                tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
                                tileSize: 256,
                                encoding: "terrarium",
                                maxzoom: 14
                            },
                            track: {
                                type: "geojson",
                                data: {
                                    type: "Feature",
                                    geometry: {type: "LineString", coordinates: coordinates}
                                }
                            }
                        },
                        layers: [
                            {id: "satellite", type: "raster", source: "satellite"},
                            {
                                id: "track-line",
                                type: "line",
                                source: "track",
                                paint: {
                                    "line-color": "#10b981",
                                    "line-width": 4,
                                    "line-opacity": 0.95
                                }
                            }
                        ],
                        terrain: {source: "terrain", exaggeration: 1.4}
                    },
                    maxPitch: 80
                });

                map3d.addControl(new maplibregl.NavigationControl({visualizePitch: true}));
                map3d.on("load", function () {
                    map3d.fitBounds(bounds, {padding: 60, pitch: 62, duration: 0});
                });
                map3dReady = true;
            })
            .catch(function () {
                map3dElement.innerHTML =
                    '<div class="d-flex align-items-center justify-content-center h-100 text-muted small">' +
                    "No se ha podido cargar la vista 3D.</div>";
            });
    }

    /* ---------- Conmutación 2D / 3D ---------- */

    button3d.addEventListener("click", function () {
        map2dElement.classList.add("d-none");
        map3dElement.classList.remove("d-none");
        button3d.classList.add("active");
        button2d.classList.remove("active");
        if (!map3dReady) init3d();
    });

    button2d.addEventListener("click", function () {
        map3dElement.classList.add("d-none");
        map2dElement.classList.remove("d-none");
        button2d.classList.add("active");
        button3d.classList.remove("active");
        map.invalidateSize();
        if (trackBounds) map.fitBounds(trackBounds);
    });
}
