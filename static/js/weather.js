/* Parte meteorológico de la actividad, con datos de Open-Meteo
   (https://open-meteo.com, gratuito y sin clave de API).
   Si la fecha de la actividad está dentro del horizonte de previsión
   (16 días) se muestra la previsión de ese día; si no, el tiempo actual
   en la zona y los próximos días. */

function initCordadaWeather(options) {
    const container = document.getElementById(options.containerId || "weather-box");

    const WEATHER_CODES = {
        0: {icon: "sun", text: "Despejado"},
        1: {icon: "sun", text: "Poco nuboso"},
        2: {icon: "cloud", text: "Parcialmente nuboso"},
        3: {icon: "cloud", text: "Cubierto"},
        45: {icon: "mist", text: "Niebla"},
        48: {icon: "mist", text: "Niebla con cencellada"},
        51: {icon: "cloud-rain", text: "Llovizna débil"},
        53: {icon: "cloud-rain", text: "Llovizna"},
        55: {icon: "cloud-rain", text: "Llovizna intensa"},
        56: {icon: "cloud-rain", text: "Llovizna helada"},
        57: {icon: "cloud-rain", text: "Llovizna helada intensa"},
        61: {icon: "cloud-rain", text: "Lluvia débil"},
        63: {icon: "cloud-rain", text: "Lluvia"},
        65: {icon: "cloud-rain", text: "Lluvia fuerte"},
        66: {icon: "cloud-rain", text: "Lluvia helada"},
        67: {icon: "cloud-rain", text: "Lluvia helada fuerte"},
        71: {icon: "cloud-snow", text: "Nevada débil"},
        73: {icon: "cloud-snow", text: "Nevada"},
        75: {icon: "cloud-snow", text: "Nevada fuerte"},
        77: {icon: "cloud-snow", text: "Cinarra"},
        80: {icon: "cloud-rain", text: "Chubascos débiles"},
        81: {icon: "cloud-rain", text: "Chubascos"},
        82: {icon: "cloud-rain", text: "Chubascos fuertes"},
        85: {icon: "cloud-snow", text: "Chubascos de nieve"},
        86: {icon: "cloud-snow", text: "Chubascos de nieve fuertes"},
        95: {icon: "cloud-storm", text: "Tormenta"},
        96: {icon: "cloud-storm", text: "Tormenta con granizo"},
        99: {icon: "cloud-storm", text: "Tormenta con granizo fuerte"}
    };

    function describe(code) {
        return WEATHER_CODES[code] || {icon: "cloud", text: "Variable"};
    }

    function dayLabel(isoDate) {
        const date = new Date(isoDate + "T12:00:00");
        return date.toLocaleDateString("es-ES", {weekday: "short", day: "numeric", month: "short"});
    }

    function dayCard(daily, index, highlight) {
        const info = describe(daily.weather_code[index]);
        return '<div class="weather-day' + (highlight ? " highlight" : "") + '">' +
            '<div class="small text-muted">' + dayLabel(daily.time[index]) + '</div>' +
            '<i class="ti ti-' + info.icon + '"></i>' +
            '<div class="small">' + info.text + '</div>' +
            '<div class="fw-semibold small">' +
                Math.round(daily.temperature_2m_max[index]) + '° / ' +
                Math.round(daily.temperature_2m_min[index]) + '°' +
            '</div>' +
            '<div class="small text-muted">' +
                '<i class="ti ti-droplet me-1"></i>' + (daily.precipitation_probability_max[index] ?? "–") + '%' +
                ' · <i class="ti ti-wind me-1"></i>' + Math.round(daily.wind_speed_10m_max[index]) + ' km/h' +
            '</div>' +
        '</div>';
    }

    const url = "https://api.open-meteo.com/v1/forecast" +
        "?latitude=" + options.lat + "&longitude=" + options.lon +
        "&daily=weather_code,temperature_2m_max,temperature_2m_min," +
        "precipitation_probability_max,wind_speed_10m_max" +
        "&current=temperature_2m,weather_code,wind_speed_10m" +
        "&timezone=auto&forecast_days=16";

    fetch(url)
        .then(function (response) {
            if (!response.ok) throw new Error("weather http " + response.status);
            return response.json();
        })
        .then(function (data) {
            const daily = data.daily;
            const activityIndex = daily.time.indexOf(options.activityDate);
            let html = "";

            if (activityIndex >= 0) {
                const from = Math.max(0, Math.min(activityIndex - 1, daily.time.length - 4));
                const to = Math.min(daily.time.length, from + 4);
                html += '<div class="small text-muted mb-2">' +
                    '<i class="ti ti-calendar me-1"></i>Previsión para el día de la actividad</div>';
                html += '<div class="weather-strip">';
                for (let index = from; index < to; index++) {
                    html += dayCard(daily, index, index === activityIndex);
                }
                html += "</div>";
            } else {
                const current = describe(data.current.weather_code);
                html += '<div class="small text-muted mb-2">' +
                    'La actividad está fuera del horizonte de previsión (16 días). ' +
                    'Tiempo actual en la zona:</div>';
                html += '<div class="d-flex align-items-center gap-2 mb-3">' +
                    '<i class="ti ti-' + current.icon + '" style="font-size: 1.8rem;"></i>' +
                    '<span class="fw-semibold">' + Math.round(data.current.temperature_2m) + ' °C · ' +
                    current.text + '</span>' +
                    '<span class="text-muted small"><i class="ti ti-wind me-1"></i>' +
                    Math.round(data.current.wind_speed_10m) + ' km/h</span>' +
                '</div>';
                html += '<div class="weather-strip">';
                for (let index = 0; index < Math.min(4, daily.time.length); index++) {
                    html += dayCard(daily, index, false);
                }
                html += "</div>";
            }
            html += '<div class="text-end small text-muted mt-2">Datos: Open-Meteo</div>';
            container.innerHTML = html;
        })
        .catch(function () {
            container.innerHTML = '<div class="text-muted small">' +
                'No se ha podido cargar el parte meteorológico.</div>';
        });
}
