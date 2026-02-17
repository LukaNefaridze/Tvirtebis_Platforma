import logging
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


class SafeAdminMixin:
    """
    Safety-net mixin for Django admin classes.
    Catches unhandled ValidationError and database errors in admin views
    and displays them as inline admin messages instead of ugly crash pages.

    Usage: Place BEFORE ModelAdmin in the class definition MRO:
        class MyAdmin(SafeAdminMixin, ModelAdmin):
            ...
    """

    def _handle_exception(self, request, exc):
        """Convert an exception into a user-friendly admin error message."""
        if isinstance(exc, ValidationError):
            error_msg = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
        else:
            error_msg = str(exc)
        self.message_user(request, error_msg, messages.ERROR)
        logger.exception("Admin error caught by SafeAdminMixin: %s", error_msg)

    def changelist_view(self, request, extra_context=None):
        try:
            return super().changelist_view(request, extra_context)
        except (ValidationError, IntegrityError, ValueError) as e:
            self._handle_exception(request, e)
            return redirect(request.get_full_path())

    def change_view(self, request, object_id, form_url='', extra_context=None):
        try:
            return super().change_view(request, object_id, form_url, extra_context)
        except (ValidationError, IntegrityError, ValueError) as e:
            self._handle_exception(request, e)
            return redirect(request.get_full_path())

    def add_view(self, request, form_url='', extra_context=None):
        try:
            return super().add_view(request, form_url, extra_context)
        except (ValidationError, IntegrityError, ValueError) as e:
            self._handle_exception(request, e)
            return redirect(request.get_full_path())
