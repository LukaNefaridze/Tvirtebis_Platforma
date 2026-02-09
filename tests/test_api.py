from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import AdminUser, User
from apps.metadata.models import Currency, CargoType, TransportType, VolumeUnit
from apps.bids.models import Platform, PlatformAPIKey, Bid
from apps.shipments.models import Shipment


class APITestCase(TestCase):
    """Base test case for API tests."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create admin
        self.admin = AdminUser.objects.create_superuser(
            email='admin@test.com',
            password='TestPass123!',
            first_name='Admin',
            last_name='User'
        )
        
        # Create user
        self.user = User.objects.create_user(
            email='user@test.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            personal_id='12345678901',
            mobile='+995555123456',
            created_by_admin=self.admin
        )
        
        # Create metadata
        self.currency = Currency.objects.create(code='GEL', name='Lari', symbol='₾')
        self.cargo_type = CargoType.objects.create(name='Food')
        self.transport_type = TransportType.objects.create(name='Truck')
        self.volume_unit = VolumeUnit.objects.create(name='Kilogram', abbreviation='kg')
        
        # Create platform and API key
        self.platform = Platform.objects.create(
            company_name='Test Platform',
            contact_email='platform@test.com',
            contact_phone='+995555999888'
        )
        
        self.raw_api_key = PlatformAPIKey.generate_key()
        self.api_key = PlatformAPIKey(platform=self.platform)
        self.api_key.set_key(self.raw_api_key)
        self.api_key.save()
        
        # Create shipment
        future_date = timezone.now() + timedelta(days=1)
        self.shipment = Shipment.objects.create(
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


class MetadataAPITestCase(APITestCase):
    """Test metadata API endpoint."""
    
    def test_get_metadata_no_auth(self):
        """Test getting metadata without authentication."""
        response = self.client.get('/api/v1/metadata/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('cargo_types', response.data['data'])
        self.assertIn('transport_types', response.data['data'])
        self.assertIn('volume_units', response.data['data'])
        self.assertIn('currencies', response.data['data'])


class ShipmentAPITestCase(APITestCase):
    """Test shipment API endpoints."""
    
    def test_list_shipments_requires_auth(self):
        """Test that listing shipments requires authentication."""
        response = self.client.get('/api/v1/shipments/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_shipments_with_auth(self):
        """Test listing shipments with authentication."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.raw_api_key}')
        response = self.client.get('/api/v1/shipments/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('shipments', response.data['data'])
    
    def test_get_shipment_detail(self):
        """Test getting shipment detail."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.raw_api_key}')
        response = self.client.get(f'/api/v1/shipments/{self.shipment.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['id'], str(self.shipment.id))


class BidAPITestCase(APITestCase):
    """Test bid API endpoints."""
    
    def test_create_bid_requires_auth(self):
        """Test that creating bid requires authentication."""
        response = self.client.post(
            f'/api/v1/shipments/{self.shipment.id}/bids/',
            data={}
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_bid_success(self):
        """Test successful bid creation."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.raw_api_key}')
        
        bid_data = {
            'company_name': 'Test Transport Ltd',
            'price': '250.00',
            'currency': 'GEL',
            'estimated_delivery_time': 6,
            'comment': 'Fast delivery',
            'contact_person': 'John Doe',
            'contact_phone': '+995555999888',
            'driver_id': 'driver-001'
        }
        
        response = self.client.post(
            f'/api/v1/shipments/{self.shipment.id}/bids/',
            data=bid_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('bid_id', response.data['data'])
    
    def test_create_bid_wrong_currency(self):
        """Test bid creation with wrong currency."""
        # Create another currency
        Currency.objects.create(code='USD', name='Dollar', symbol='$')
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.raw_api_key}')
        
        bid_data = {
            'company_name': 'Test Transport Ltd',
            'price': '250.00',
            'currency': 'USD',  # Wrong currency
            'estimated_delivery_time': 6,
            'contact_person': 'John Doe',
            'contact_phone': '+995555999888',
            'driver_id': 'driver-001'
        }
        
        response = self.client.post(
            f'/api/v1/shipments/{self.shipment.id}/bids/',
            data=bid_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_cannot_submit_duplicate_rejected_bid(self):
        """Test that exact duplicate of rejected bid cannot be resubmitted."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.raw_api_key}')
        
        bid_data = {
            'company_name': 'Test Transport Ltd',
            'price': '250.00',
            'currency': 'GEL',
            'estimated_delivery_time': 6,
            'contact_person': 'John Doe',
            'contact_phone': '+995555999888',
            'driver_id': 'driver-001'
        }
        
        # Create first bid
        response = self.client.post(
            f'/api/v1/shipments/{self.shipment.id}/bids/',
            data=bid_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        bid_id = response.data['data']['bid_id']
        
        # Reject the bid
        bid = Bid.objects.get(id=bid_id)
        bid.reject()
        
        # Try to submit exact same bid again
        response = self.client.post(
            f'/api/v1/shipments/{self.shipment.id}/bids/',
            data=bid_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['error']['code'], 'BID_DUPLICATE')
