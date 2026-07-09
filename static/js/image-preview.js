/* Previsualización de imágenes antes de subirlas.
   Se engancha automáticamente a cualquier <input type="file"> que acepte
   imágenes y muestra una tira de miniaturas junto al campo, en toda la
   plataforma (feed, perfil, mercado, fotos de actividad...). */

(function () {
    function acceptsImages(input) {
        if (input.type !== "file") return false;
        const accept = input.getAttribute("accept") || "";
        return accept.includes("image");
    }

    function anchorFor(input) {
        // Si el input vive dentro de un botón-etiqueta (como en el feed),
        // la tira se coloca después de la etiqueta para que sea visible.
        return input.closest("label") || input;
    }

    function renderPreview(input) {
        const anchor = anchorFor(input);
        let strip = anchor.parentElement.querySelector(".upload-preview");
        if (strip) {
            strip.querySelectorAll("img").forEach(function (img) {
                URL.revokeObjectURL(img.src);
            });
            strip.remove();
        }
        if (!input.files || input.files.length === 0) return;

        strip = document.createElement("div");
        strip.className = "upload-preview";
        Array.from(input.files).forEach(function (file) {
            if (!file.type.startsWith("image/")) return;
            const img = document.createElement("img");
            img.src = URL.createObjectURL(file);
            img.alt = file.name;
            img.title = file.name;
            strip.appendChild(img);
        });
        if (strip.children.length) {
            const count = document.createElement("span");
            count.className = "small text-muted align-self-center";
            count.textContent = strip.children.length === 1
                ? "1 imagen seleccionada"
                : strip.children.length + " imágenes seleccionadas";
            strip.appendChild(count);
            anchor.insertAdjacentElement("afterend", strip);
        }
    }

    document.addEventListener("change", function (event) {
        if (acceptsImages(event.target)) renderPreview(event.target);
    });
})();
