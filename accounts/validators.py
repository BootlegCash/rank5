# In accounts/validators.py
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re

class UppercaseValidator:
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("This password must contain at least one uppercase letter."),
                code='password_no_upper',
            )

    def get_help_text(self):
        return _("Your password must contain at least one uppercase letter.")

class AllowedCharactersValidator:
    def validate(self, password, user=None):
        # Allows letters (a-z, A-Z), numbers (0-9), and !, $, ?
        # Disallows any other character.
        if not re.match(r"^[a-zA-Z0-9!$?]+$", password):
            raise ValidationError(
                _("Password can only contain letters, numbers, and the special characters: !, $, ?"),
                code='password_invalid_characters',
            )
    def get_help_text(self):
        return _("Your password can only contain letters, numbers, and the special characters: !, $, ?")