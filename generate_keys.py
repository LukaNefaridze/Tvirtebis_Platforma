# generate_keys.py
from django.core.management.utils import get_random_secret_key
from cryptography.fernet import Fernet

secret_key = get_random_secret_key()
field_key = Fernet.generate_key().decode()

with open(".env", "w") as f:
    f.write(f"SECRET_KEY={secret_key}\n")
    f.write(f"FIELD_ENCRYPTION_KEY={field_key}\n")
    f.write(f"ALLOWED_HOSTS=127.0.0.1,localhost,192.168.80.230\n")

print("✅ Generated .env file with SECRET_KEY, FIELD_ENCRYPTION_KEY and ALLOWED_HOSTS")
