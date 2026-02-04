from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from apps.accounts.models import User
from apps.accounts.utils import generate_temporary_password, validate_personal_id, validate_mobile_number
from apps.metadata.models import Currency, CargoType, TransportType, VolumeUnit
from apps.bids.models import Platform, PlatformAPIKey, Bid, RejectedBidCache
from apps.shipments.models import Shipment


class UtilsTestCase(TestCase):
    """Test utility functions."""
    
    def test_generate_temporary_password(self):
        """Test temporary password generation."""
        password = generate_temporary_password()
        self.assertEqual(len(password), 8)
        self.assertTrue(any(c.isupper() for c in password))
        self.assertTrue(any(c.islower() for c in password))
        self.assertTrue(any(c.isdigit() for c in password))
        self.assertTrue(any(c in '!@#$%^&*' for c in password))
    
    def test_validate_personal_id(self):
        """Test personal ID validation."""
        # Valid
        self.assertEqual(validate_personal_id('12345678901'), '12345678901')
        
        # Invalid
        with self.assertRaises(ValidationError):
            validate_personal_id('123')  # Too short
        
        with self.assertRaises(ValidationError):
            validate_personal_id('abcdefghijk')  # Not digits
    
    def test_validate_mobile_number(self):
        """Test mobile number validation."""
        # Valid formats
        self.assertIsNotNone(validate_mobile_number('+995555123456'))
        self.assertIsNotNone(validate_mobile_number('555123456'))
        
        # Invalid
        with self.assertRaises(ValidationError):
            validate_mobile_number('123')
        
        with self.assertRaises(ValidationError):
            validate_mobile_number('888123456')  # Doesn't start with 5


class UserModelTestCase(TestCase):
    """Test User model."""
    
    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_superuser(
            email='admin@test.com',
            password='TestPass123!',
            first_name='Admin',
            last_name='User'
        )
    
    def test_create_user(self):
        """Test user creation."""
        user = User.objects.create_user(
            email='user@test.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            personal_id='12345678901',
            mobile='+995555123456'
        )
        
        self.assertEqual(user.email, 'user@test.com')
        self.assertTrue(user.check_password('TestPass123!'))
        self.assertEqual(user.get_full_name(), 'Test User')


class ShipmentModelTestCase(TestCase):
    """Test Shipment model."""
    
    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_superuser(
            email='admin@test.com',
            password='TestPass123!',
            first_name='Admin',
            last_name='User'
        )
        
        self.user = User.objects.create_user(
            email='user@test.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            personal_id='12345678901',
            mobile='+995555123456'
        )
        
        self.currency = Currency.objects.create(code='GEL', name='Lari', symbol='₾')
        self.cargo_type = CargoType.objects.create(name='Food')
        self.transport_type = TransportType.objects.create(name='Truck')
        self.volume_unit = VolumeUnit.objects.create(name='Kilogram', abbreviation='kg')
    
    def test_create_shipment(self):
        """Test shipment creation."""
        future_date = timezone.now() + timedelta(days=1)
        
        shipment = Shipment.objects.create(
            user=self.user,
            pickup_location='Tbilisi, Rustaveli 1',
            pickup_date=future_date,
            delivery_location='Batumi, Ninoshvili 2',
            cargo_type=self.cargo_type,
            cargo_volume=Decimal('100.50'),
            volume_unit=self.volume_unit,
            transport_type=self.transport_type,
            preferred_currency=self.currency
        )
        
        self.assertEqual(shipment.status, 'active')
        self.assertEqual(shipment.user, self.user)
        self.assertEqual(shipment.bids_count, 0)
    
    def test_shipment_mark_completed(self):
        """Test marking shipment as completed."""
        future_date = timezone.now() + timedelta(days=1)
        
        shipment = Shipment.objects.create(
            user=self.user,
            pickup_location='Tbilisi',
            pickup_date=future_date,
            delivery_location='Batumi',
            cargo_type=self.cargo_type,
            cargo_volume=Decimal('100'),
            volume_unit=self.volume_unit,
            transport_type=self.transport_type,
            preferred_currency=self.currency
        )
        
        platform = Platform.objects.create(
            company_name='Test Platform',
            contact_email='platform@test.com',
            contact_phone='+995555999888'
        )
        
        bid = Bid.objects.create(
            shipment=shipment,
            platform=platform,
            company_name='Test Company',
            price=Decimal('250.00'),
            currency=self.currency,
            estimated_delivery_time=6,
            contact_person='John Doe',
            contact_phone='+995555999888'
        )
        
        shipment.mark_completed(bid)
        
        shipment.refresh_from_db()
        bid.refresh_from_db()
        
        self.assertEqual(shipment.status, 'completed')
        self.assertEqual(bid.status, 'accepted')
        self.assertEqual(shipment.selected_bid, bid)


class BidModelTestCase(TestCase):
    """Test Bid model."""
    
    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_superuser(
            email='admin@test.com',
            password='TestPass123!',
            first_name='Admin',
            last_name='User'
        )
        
        self.user = User.objects.create_user(
            email='user@test.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            personal_id='12345678901',
            mobile='+995555123456'
        )
        
        self.currency = Currency.objects.create(code='GEL', name='Lari', symbol='₾')
        self.cargo_type = CargoType.objects.create(name='Food')
        self.transport_type = TransportType.objects.create(name='Truck')
        self.volume_unit = VolumeUnit.objects.create(name='Kilogram', abbreviation='kg')
        
        future_date = timezone.now() + timedelta(days=1)
        self.shipment = Shipment.objects.create(
            user=self.user,
            pickup_location='Tbilisi',
            pickup_date=future_date,
            delivery_location='Batumi',
            cargo_type=self.cargo_type,
            cargo_volume=Decimal('100'),
            volume_unit=self.volume_unit,
            transport_type=self.transport_type,
            preferred_currency=self.currency
        )
        
        self.platform = Platform.objects.create(
            company_name='Test Platform',
            contact_email='platform@test.com',
            contact_phone='+995555999888'
        )
    
    def test_create_bid(self):
        """Test bid creation."""
        bid = Bid.objects.create(
            shipment=self.shipment,
            platform=self.platform,
            company_name='Test Company',
            price=Decimal('250.00'),
            currency=self.currency,
            estimated_delivery_time=6,
            contact_person='John Doe',
            contact_phone='+995555999888'
        )
        
        self.assertEqual(bid.status, 'pending')
        self.assertEqual(bid.shipment, self.shipment)
        self.assertEqual(bid.platform, self.platform)
    
    def test_bid_rejection_creates_cache(self):
        """Test that rejecting a bid creates cache entry."""
        bid = Bid.objects.create(
            shipment=self.shipment,
            platform=self.platform,
            company_name='Test Company',
            price=Decimal('250.00'),
            currency=self.currency,
            estimated_delivery_time=6,
            contact_person='John Doe',
            contact_phone='+995555999888'
        )
        
        bid.reject()
        
        # Check cache entry exists
        cache_exists = RejectedBidCache.objects.filter(
            shipment=self.shipment,
            platform=self.platform,
            price=Decimal('250.00'),
            estimated_delivery_time=6,
            currency=self.currency
        ).exists()
        
        self.assertTrue(cache_exists)
    
    def test_can_submit_bid_validation(self):
        """Test bid submission validation."""
        # Should be able to submit first bid
        can_submit, error_code, error_msg = Bid.objects.can_submit_bid(
            shipment=self.shipment,
            platform=self.platform,
            price=Decimal('250.00'),
            estimated_delivery_time=6,
            currency=self.currency,
            company_name='Test Company'
        )
        
        self.assertTrue(can_submit)
        
        # Create and reject a bid
        bid = Bid.objects.create(
            shipment=self.shipment,
            platform=self.platform,
            company_name='Test Company',
            price=Decimal('250.00'),
            currency=self.currency,
            estimated_delivery_time=6,
            contact_person='John Doe',
            contact_phone='+995555999888'
        )
        bid.reject()
        
        # Should not be able to submit exact duplicate
        can_submit, error_code, error_msg = Bid.objects.can_submit_bid(
            shipment=self.shipment,
            platform=self.platform,
            price=Decimal('250.00'),
            estimated_delivery_time=6,
            currency=self.currency,
            company_name='Test Company'
        )
        
        self.assertFalse(can_submit)
        self.assertEqual(error_code, 'BID_DUPLICATE')


class PlatformAPIKeyTestCase(TestCase):
    """Test PlatformAPIKey model."""
    
    def setUp(self):
        """Set up test data."""
        self.platform = Platform.objects.create(
            company_name='Test Platform',
            contact_email='platform@test.com',
            contact_phone='+995555999888'
        )
    
    def test_generate_api_key(self):
        """Test API key generation."""
        raw_key = PlatformAPIKey.generate_key()
        
        self.assertIsNotNone(raw_key)
        self.assertGreater(len(raw_key), 20)
    
    def test_check_api_key(self):
        """Test API key verification."""
        raw_key = PlatformAPIKey.generate_key()
        
        api_key = PlatformAPIKey(platform=self.platform)
        api_key.set_key(raw_key)
        api_key.save()
        
        # Should verify correctly
        self.assertTrue(api_key.check_key(raw_key))
        
        # Should not verify with wrong key
        self.assertFalse(api_key.check_key('wrong_key'))
