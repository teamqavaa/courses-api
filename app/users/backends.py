from django.contrib.auth.backends import ModelBackend

from .models import User


class EmailOrPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        # Case-insensitive email match; filter().first() also tolerates legacy
        # rows stored with mixed case instead of falling over on duplicates.
        if "@" in username:
            lookup = {"email__iexact": username}
        else:
            lookup = {"phone": username}

        user = User.objects.filter(**lookup).first()

        if user is None or not user.check_password(password):
            return None
        if self.user_can_authenticate(user):
            return user
        return None
