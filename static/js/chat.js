/* Chat de Cordada: carga de mensajes, envío y refresco automático.
   Se usa tanto en el chat de actividades como en el del mercado. */

function initCordadaChat(options) {
    const box = document.getElementById(options.boxId || "chat-box");
    const form = document.getElementById(options.formId || "chat-form");
    const input = document.getElementById(options.inputId || "chat-input");
    let lastCount = -1;

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function render(messages) {
        if (messages.length === lastCount) return;
        lastCount = messages.length;
        if (messages.length === 0) {
            box.innerHTML = '<div class="text-center text-muted small py-4">' +
                (options.emptyText || "Todavía no hay mensajes. ¡Rompe el hielo!") +
                "</div>";
            return;
        }
        box.innerHTML = messages.map(function (message) {
            return '<div class="chat-message' + (message.mine ? " mine" : "") + '">' +
                '<div class="d-flex align-items-end gap-2">' +
                (message.mine ? "" :
                    '<span class="avatar-circle" style="width:1.75rem;height:1.75rem;font-size:0.7rem;">' +
                    escapeHtml(message.initial) + '</span>') +
                '<div class="chat-bubble">' +
                (message.mine ? "" :
                    '<div class="fw-semibold small">' + escapeHtml(message.author) + '</div>') +
                '<div>' + escapeHtml(message.content) + '</div>' +
                '<div class="small ' + (message.mine ? "text-white-50" : "text-muted") + '">' +
                message.created + '</div>' +
                '</div></div></div>';
        }).join("");
        box.scrollTop = box.scrollHeight;
    }

    function load() {
        fetch(options.messagesUrl)
            .then(function (response) { return response.json(); })
            .then(function (data) { render(data.messages); })
            .catch(function () { /* se reintenta en el siguiente ciclo */ });
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        const content = input.value.trim();
        if (!content) return;
        fetch(options.sendUrl, {
            method: "POST",
            headers: {"X-CSRFToken": options.csrfToken},
            body: new URLSearchParams({content: content})
        }).then(function (response) {
            if (response.ok) {
                input.value = "";
                load();
            }
        });
    });

    load();
    setInterval(load, options.pollInterval || 5000);
}
