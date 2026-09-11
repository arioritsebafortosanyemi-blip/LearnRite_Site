(function () {
    "use strict";

    function getCookie(name) {
        const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
        return match ? decodeURIComponent(match[2]) : null;
    }

    function showToast(message, isError) {
        let container = document.getElementById("site-toast-container");
        if (!container) {
            container = document.createElement("div");
            container.id = "site-toast-container";
            document.body.appendChild(container);
        }
        const toast = document.createElement("div");
        toast.className = "site-toast" + (isError ? " site-toast-error" : "");
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(function () {
            toast.remove();
        }, 3000);
    }

    function updateCartBadge(count) {
        const badge = document.getElementById("cart-count-badge");
        if (!badge) {
            return;
        }
        badge.textContent = count;
        badge.hidden = !count;
    }

    function postForm(form) {
        return fetch(form.getAttribute("action"), {
            method: "POST",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: new FormData(form),
        }).then(function (response) {
            return response.json().then(function (data) {
                return { ok: response.ok, data: data };
            });
        });
    }

    // Clicking a star rates immediately - no separate "Submit" click needed.
    document.addEventListener("change", function (event) {
        const input = event.target;
        if (input.matches("[data-ajax='review'] input[type='radio'][name='rating']")) {
            input.closest("form").requestSubmit();
        }
    });

    document.addEventListener("submit", function (event) {
        const form = event.target;

        if (form.matches("[data-ajax='add-to-cart']")) {
            event.preventDefault();
            const button = form.querySelector("button[type='submit']");
            const originalText = button.textContent;
            button.disabled = true;
            postForm(form)
                .then(function (result) {
                    showToast(result.data.message, !result.ok);
                    if (result.ok) {
                        updateCartBadge(result.data.cart_count);
                        button.textContent = "Added!";
                        setTimeout(function () {
                            button.textContent = originalText;
                        }, 1500);
                    }
                })
                .catch(function () {
                    showToast("Something went wrong. Please try again.", true);
                })
                .finally(function () {
                    button.disabled = false;
                });
        }

        if (form.matches("[data-ajax='wishlist-toggle']")) {
            event.preventDefault();
            const button = form.querySelector("button[type='submit']");
            postForm(form)
                .then(function (result) {
                    showToast(result.data.message, !result.ok);
                    if (result.ok) {
                        button.innerHTML = result.data.wishlisted
                            ? '<i class="bi bi-heart-fill text-danger"></i> Saved'
                            : '<i class="bi bi-heart"></i> Save';
                    }
                })
                .catch(function () {
                    showToast("Something went wrong. Please try again.", true);
                });
        }

        if (form.matches("[data-ajax='review']")) {
            event.preventDefault();
            const button = form.querySelector("button[type='submit']");
            postForm(form)
                .then(function (result) {
                    showToast(result.data.message, !result.ok);
                    if (result.ok) {
                        button.textContent = "Update Rating";
                    }
                })
                .catch(function () {
                    showToast("Something went wrong. Please try again.", true);
                });
        }
    });
})();
