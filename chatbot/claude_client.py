import anthropic
from django.conf import settings

_client = None


def get_client():
    """Lazy singleton - constructing anthropic.Anthropic() reads env/config
    at call time, not import time, so it can't break app startup if the
    key is briefly unset."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client
