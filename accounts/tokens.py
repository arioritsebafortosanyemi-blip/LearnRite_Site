from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """Same signed-timestamp approach as Django's password-reset token, but
    keyed off whether the profile is already verified - so a link becomes
    invalid the moment it's used, same as a password-reset link does after
    the password changes."""

    def _make_hash_value(self, user, timestamp):
        profile = getattr(user, "profile", None)
        verified = profile.email_verified if profile else False
        return f"{user.pk}{user.email}{verified}{timestamp}"


email_verification_token = EmailVerificationTokenGenerator()
