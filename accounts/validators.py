import re

from django.core.exceptions import ValidationError


class UppercaseStartValidator:
    """Requires the password to start with an uppercase letter."""

    def validate(self, password, user=None):
        if not password or not password[0].isupper():
            raise ValidationError(
                "Password must start with an uppercase letter.",
                code="password_no_upper_start",
            )

    def get_help_text(self):
        return "Your password must start with an uppercase letter."


class SymbolValidator:
    """Requires the password to contain at least one non-alphanumeric symbol."""

    SYMBOL_RE = re.compile(r"[^A-Za-z0-9]")

    def validate(self, password, user=None):
        if not self.SYMBOL_RE.search(password or ""):
            raise ValidationError(
                "Password must contain at least one symbol (e.g. !, @, #, $, %).",
                code="password_no_symbol",
            )

    def get_help_text(self):
        return "Your password must contain at least one symbol (e.g. !, @, #, $, %)."
