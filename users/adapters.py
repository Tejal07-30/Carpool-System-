from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.exceptions import PermissionDenied

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def presociallogin(self, request, sociallogin):
        email = sociallogin.user.email

        if not email.endswith("@pilani.bits-pilani.ac.in"):
            raise PermissionDenied("Only BITS emails allowed")