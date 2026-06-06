from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import SignupClosedException
from django.contrib import messages


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        email = sociallogin.user.email
        if not email.endswith('@pilani.bits-pilani.ac.in'):
            messages.error(
                request,
                'Only BITS Pilani (@pilani.bits-pilani.ac.in) email addresses are allowed.'
            )
            raise SignupClosedException()

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        if not user.role or user.role not in ('driver', 'admin'):
            user.role = 'passenger'
            user.save(update_fields=['role'])
        return user