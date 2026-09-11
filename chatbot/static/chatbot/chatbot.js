(function () {
    "use strict";

    function getCookie(name) {
        const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
        return match ? decodeURIComponent(match[2]) : null;
    }

    const toggle = document.getElementById("chatbot-toggle");
    const closeBtn = document.getElementById("chatbot-close");
    const panel = document.getElementById("chatbot-panel");
    const messagesEl = document.getElementById("chatbot-messages");
    const form = document.getElementById("chatbot-form");
    const input = document.getElementById("chatbot-input");

    let history = [];
    let sending = false;

    function addBubble(text, who) {
        const bubble = document.createElement("div");
        bubble.className = "chatbot-bubble chatbot-bubble-" + who;
        bubble.textContent = text;
        messagesEl.appendChild(bubble);
        messagesEl.scrollTop = messagesEl.scrollHeight;
        return bubble;
    }

    toggle.addEventListener("click", function () {
        panel.hidden = !panel.hidden;
        if (!panel.hidden) {
            input.focus();
            if (!messagesEl.children.length) {
                addBubble("Hi! Ask me about pricing, shipping, payment, or your order.", "bot");
            }
        }
    });

    closeBtn.addEventListener("click", function () {
        panel.hidden = true;
    });

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        const message = input.value.trim();
        if (!message || sending) {
            return;
        }
        sending = true;
        addBubble(message, "user");
        input.value = "";
        const thinking = addBubble("...", "bot");

        fetch(window.CHATBOT_CHAT_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({ message: message, history: history }),
        })
            .then(function (response) {
                return response.json().then(function (data) {
                    return { ok: response.ok, data: data };
                });
            })
            .then(function (result) {
                thinking.remove();
                if (!result.ok) {
                    addBubble(result.data.error || "Something went wrong. Please try again.", "bot");
                    return;
                }
                addBubble(result.data.reply, "bot");
                history = result.data.history || history;
            })
            .catch(function () {
                thinking.remove();
                addBubble("Couldn't reach the chatbot. Please check your connection and try again.", "bot");
            })
            .finally(function () {
                sending = false;
            });
    });
})();
