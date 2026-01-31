from django.core.management.base import BaseCommand
from django.db import transaction
from apps.metadata.models import Currency, CargoType, TransportType, VolumeUnit
from apps.accounts.models import AdminUser
import getpass


class Command(BaseCommand):
    help = 'Setup initial data for the platform (currencies, cargo types, transport types, volume units, and superadmin)'
    
    def handle(self, *args, **options):
        """Setup initial data."""
        self.stdout.write(self.style.SUCCESS('Setting up initial data...'))
        
        with transaction.atomic():
            # Create currencies
            self.create_currencies()
            
            # Create cargo types
            self.create_cargo_types()
            
            # Create transport types
            self.create_transport_types()
            
            # Create volume units
            self.create_volume_units()
            
            # Create superadmin
            self.create_superadmin()
        
        self.stdout.write(self.style.SUCCESS('Initial data setup completed successfully!'))
    
    def create_currencies(self):
        """Create default currencies."""
        currencies_data = [
            {'code': 'GEL', 'name': 'ქართული ლარი', 'symbol': '₾', 'sort_order': 1},
            {'code': 'USD', 'name': 'ამერიკული დოლარი', 'symbol': '$', 'sort_order': 2},
            {'code': 'EUR', 'name': 'ევრო', 'symbol': '€', 'sort_order': 3},
        ]
        
        for data in currencies_data:
            currency, created = Currency.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'symbol': data['symbol'],
                    'sort_order': data['sort_order'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created currency: {currency.code}'))
            else:
                self.stdout.write(f'  - Currency already exists: {currency.code}')
    
    def create_cargo_types(self):
        """Create default cargo types."""
        cargo_types_data = [
            {'name': 'საკვები პროდუქტები', 'sort_order': 1},
            {'name': 'სამშენებლო მასალები', 'sort_order': 2},
            {'name': 'ავეჯი', 'sort_order': 3},
            {'name': 'ტექნიკა', 'sort_order': 4},
            {'name': 'ტანსაცმელი და ქსოვილები', 'sort_order': 5},
            {'name': 'ქიმიური საშუალებები', 'sort_order': 6},
            {'name': 'სხვა', 'sort_order': 99},
        ]
        
        for data in cargo_types_data:
            cargo_type, created = CargoType.objects.get_or_create(
                name=data['name'],
                defaults={
                    'sort_order': data['sort_order'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created cargo type: {cargo_type.name}'))
            else:
                self.stdout.write(f'  - Cargo type already exists: {cargo_type.name}')
    
    def create_transport_types(self):
        """Create default transport types."""
        transport_types_data = [
            {'name': 'ტენტი', 'sort_order': 1},
            {'name': 'მაცივარი', 'sort_order': 2},
            {'name': 'კონტეინერი', 'sort_order': 3},
            {'name': 'ღია პლატფორმა', 'sort_order': 4},
            {'name': 'ავტომატარა', 'sort_order': 5},
            {'name': 'სხვა', 'sort_order': 99},
        ]
        
        for data in transport_types_data:
            transport_type, created = TransportType.objects.get_or_create(
                name=data['name'],
                defaults={
                    'sort_order': data['sort_order'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created transport type: {transport_type.name}'))
            else:
                self.stdout.write(f'  - Transport type already exists: {transport_type.name}')
    
    def create_volume_units(self):
        """Create default volume units."""
        volume_units_data = [
            {'name': 'კილოგრამი', 'abbreviation': 'კგ', 'sort_order': 1},
            {'name': 'ტონა', 'abbreviation': 'ტ', 'sort_order': 2},
            {'name': 'კუბური მეტრი', 'abbreviation': 'მ³', 'sort_order': 3},
            {'name': 'ლიტრი', 'abbreviation': 'ლ', 'sort_order': 4},
        ]
        
        for data in volume_units_data:
            volume_unit, created = VolumeUnit.objects.get_or_create(
                name=data['name'],
                defaults={
                    'abbreviation': data['abbreviation'],
                    'sort_order': data['sort_order'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created volume unit: {volume_unit.name}'))
            else:
                self.stdout.write(f'  - Volume unit already exists: {volume_unit.name}')
    
    def create_superadmin(self):
        """Create superadmin if it doesn't exist."""
        # Check if any superadmin exists
        if AdminUser.objects.filter(is_superuser=True).exists():
            self.stdout.write('  - Superadmin already exists')
            return
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.WARNING('SUPERADMIN CREATION'))
        self.stdout.write('=' * 50 + '\n')
        
        # Get admin details
        email = input('Enter superadmin email: ').strip()
        while not email or '@' not in email:
            self.stdout.write(self.style.ERROR('Invalid email address'))
            email = input('Enter superadmin email: ').strip()
        
        first_name = input('Enter first name: ').strip()
        while not first_name:
            self.stdout.write(self.style.ERROR('First name is required'))
            first_name = input('Enter first name: ').strip()
        
        last_name = input('Enter last name: ').strip()
        while not last_name:
            self.stdout.write(self.style.ERROR('Last name is required'))
            last_name = input('Enter last name: ').strip()
        
        # Get password
        password = getpass.getpass('Enter password: ')
        password_confirm = getpass.getpass('Confirm password: ')
        
        while password != password_confirm or len(password) < 8:
            if password != password_confirm:
                self.stdout.write(self.style.ERROR('Passwords do not match'))
            else:
                self.stdout.write(self.style.ERROR('Password must be at least 8 characters'))
            password = getpass.getpass('Enter password: ')
            password_confirm = getpass.getpass('Confirm password: ')
        
        # Create superadmin
        admin = AdminUser.objects.create_superuser(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        self.stdout.write(self.style.SUCCESS(f'\n  ✓ Superadmin created: {admin.email}'))
        self.stdout.write('=' * 50 + '\n')
