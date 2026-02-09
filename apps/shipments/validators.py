from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal


def validate_future_date(date):
    """
    Validate that the pickup date is in the future.
    """
    if date and date <= timezone.now():
        raise ValidationError(_('ტვირთის აღების თარიღი უნდა იყოს მომავალში'))
    return date


def validate_positive_decimal(value):
    """
    Validate that a decimal value is positive.
    """
    if value is not None and value <= Decimal('0'):
        raise ValidationError(_('მნიშვნელობა უნდა იყოს დადებითი'))
    return value


def validate_location(location):
    """
    Basic validation for location fields.
    """
    if not location or not location.strip():
        raise ValidationError(_('მდებარეობა სავალდებულოა'))
    
    if len(location.strip()) < 3:
        raise ValidationError(_('მდებარეობა უნდა შეიცავდეს მინიმუმ 3 სიმბოლოს'))
    
    return location.strip()
