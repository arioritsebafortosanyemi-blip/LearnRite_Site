(function () {
    var STORAGE_KEY = "learnrite_cookie_consent";
    var banner = document.getElementById("cookie-consent-banner");
    if (!banner) {
        return;
    }

    try {
        if (localStorage.getItem(STORAGE_KEY)) {
            return;
        }
    } catch (e) {
        // Storage blocked (private browsing, locked-down settings) - show
        // the banner every visit rather than hide it based on a guess.
    }

    banner.hidden = false;

    function recordChoice(choice) {
        try {
            localStorage.setItem(STORAGE_KEY, choice);
        } catch (e) {
            // Nothing to persist to - the banner will just show again next visit.
        }
        banner.hidden = true;
    }

    document.getElementById("cookie-consent-accept").addEventListener("click", function () {
        recordChoice("accepted");
    });
    document.getElementById("cookie-consent-decline").addEventListener("click", function () {
        // Only strictly necessary cookies are ever set (sign-in, cart,
        // security - see the Cookies Policy) - there's nothing non-essential
        // to actually switch off, so declining just records the preference
        // and stops asking, same as accepting.
        recordChoice("declined");
    });
})();
