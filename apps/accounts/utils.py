import random
import string
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def generate_temporary_password(length=8):
    """
    Generate a temporary password with:
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    # Define character sets
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = '!@#$%^&'  # Removed * to avoid copy-paste issues
    
    # Ensure at least one character from each set
    password = [
        random.choice(uppercase),
        random.choice(lowercase),
        random.choice(digits),
        random.choice(special)
    ]
    
    # Fill the rest randomly
    all_chars = uppercase + lowercase + digits + special
    password += [random.choice(all_chars) for _ in range(length - 4)]
    
    # Shuffle to avoid predictable pattern
    random.shuffle(password)
    
    return ''.join(password)


def validate_personal_id(personal_id):
    """
    Validate Georgian personal ID (11 digits).
    """
    if not personal_id:
        raise ValidationError(_('პირადი ნომერი სავალდებულოა'))
    
    # Remove any spaces or dashes
    personal_id = personal_id.replace(' ', '').replace('-', '')
    
    # Check if it's exactly 11 digits
    if not re.match(r'^\d{11}$', personal_id):
        raise ValidationError(_('პირადი ნომერი უნდა შეიცავდეს 11 ციფრს'))
    
    return personal_id


# Georgian mobile: 9 digits after country code, first digit of subscriber number must be 5.
# Valid: +995591325732 (13 chars), 995591325732 (12 digits), 591325732 (9 digits).
GEORGIAN_PHONE_DIGITS_AFTER_995 = 9
GEORGIAN_PHONE_MAX_LENGTH = 13  # +995 + 9 digits


def validate_mobile_number(mobile):
    """
    Validate Georgian mobile number.
    Formats: +995 5XX XX XX XX (13 chars), 995 5XX XX XX XX (12 digits), 5XX XX XX XX (9 digits).
    After 995 the next digit must be 5 (Georgian mobile prefix).
    """
    if not mobile:
        raise ValidationError(_('მობილურის ნომერი სავალდებულოა'))
    
    # Remove spaces and dashes
    mobile_clean = mobile.replace(' ', '').replace('-', '')
    
    # +995 + 9 digits (first of the 9 must be 5)
    if mobile_clean.startswith('+995'):
        if not re.match(r'^\+9955\d{8}$', mobile_clean):
            raise ValidationError(
                _('არასწორი ფორმატი. გამოიყენეთ: +995 5XX XX XX XX (სულ 13 სიმბოლო)')
            )
        return mobile
    
    # 995 + 9 digits (12 digits total; first of the 9 must be 5)
    if mobile_clean.startswith('995'):
        if not re.match(r'^9955\d{8}$', mobile_clean):
            raise ValidationError(
                _('არასწორი ფორმატი. გამოიყენეთ: 995 5XX XX XX XX (სულ 12 ციფრი)')
            )
        return mobile
    
    # 5 + 8 digits (9 digits total)
    if mobile_clean.startswith('5'):
        if not re.match(r'^5\d{8}$', mobile_clean):
            raise ValidationError(_('არასწორი ფორმატი. გამოიყენეთ: 5XX XX XX XX'))
        return mobile
    
    raise ValidationError(_('მობილური უნდა იწყებოდეს +995-ით, 995-ით ან 5-ით'))


def validate_password_strength(password):
    """
    Validate password meets requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one digit
    - At least one special character (!@#$%^&)
    """
    if len(password) < 8:
        raise ValidationError(_('პაროლი უნდა შეიცავდეს მინიმუმ 8 სიმბოლოს'))
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError(_('პაროლი უნდა შეიცავდეს მინიმუმ 1 დიდ ასოს'))
    
    if not re.search(r'\d', password):
        raise ValidationError(_('პაროლი უნდა შეიცავდეს მინიმუმ 1 რიცხვს'))
    
    if not re.search(r'[!@#$%^&]', password):
        raise ValidationError(_('პაროლი უნდა შეიცავდეს მინიმუმ 1 სპეციალურ სიმბოლოს (!@#$%^&)'))
    
    return True


def mask_personal_id(personal_id):
    """
    Mask personal ID for display (show only last 4 digits).
    Example: 01234567890 -> *******7890
    """
    if not personal_id or len(personal_id) < 4:
        return '***'
    return '*' * (len(personal_id) - 4) + personal_id[-4:]
