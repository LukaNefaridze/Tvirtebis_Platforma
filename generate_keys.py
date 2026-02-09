"""
Quick script to generate secure keys for Django.
Run: python generate_keys.py
"""
from django.core.management.utils import get_random_secret_key
import secrets

print("=" * 60)
print("GENERATED KEYS FOR .env FILE")
print("=" * 60)
print()
print("SECRET_KEY:")
print(get_random_secret_key())
print()
print("FIELD_ENCRYPTION_KEY:")
print(secrets.token_urlsafe(32))
print()
print("=" * 60)
print("Copy these values to your .env file")
print("=" * 60)
