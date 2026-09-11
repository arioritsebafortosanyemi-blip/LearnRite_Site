from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """Customers never see or choose a username, so login is by email -
    whatever they type into the (still internally-named) username field is
    looked up as an email address instead."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        try:
            user = get_user_model().objects.get(email__iexact=username)
        except get_user_model().DoesNotExist:
            return None
        except get_user_model().MultipleObjectsReturned:
            user = get_user_model().objects.filter(email__iexact=username).order_by("pk").first()
        if user and self.user_can_authenticate(user) and user.check_password(password):
            return user
        return None
