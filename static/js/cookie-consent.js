(function () {
    var STORAGE_KEY = "learnrite_cookie_consent";
    var banner = document.getElementById("cookie-consent-banner");
    if (!banner) {
        return;
    }

    try {
        if (localStorage.getItem(STORAGE_KEY) === "accepted") {
            return;
        }
    } catch (e) {
        // Storage blocked (private browsing, locked-down settings) - show
        // the banner every visit rather than hide it based on a guess.
    }

    banner.hidden = false;

    document.getElementById("cookie-consent-accept").addEventListener("click", function () {
        try {
            localStorage.setItem(STORAGE_KEY, "accepted");
        } catch (e) {
            // Nothing to persist to - the banner will just show again next visit.
        }
        banner.hidden = true;
    });
})();
