from rest_framework import serializers
from apps.metadata.models import Currency, CargoType, TransportType, VolumeUnit
from apps.shipments.models import Shipment
from apps.bids.models import Bid


class CurrencySerializer(serializers.ModelSerializer):
    """Serializer for Currency model."""
    
    class Meta:
        model = Currency
        fields = ['id', 'code', 'name', 'symbol', 'sort_order']


class CargoTypeSerializer(serializers.ModelSerializer):
    """Serializer for CargoType model."""
    
    class Meta:
        model = CargoType
        fields = ['id', 'name', 'sort_order']


class TransportTypeSerializer(serializers.ModelSerializer):
    """Serializer for TransportType model."""
    
    class Meta:
        model = TransportType
        fields = ['id', 'name', 'sort_order']


class VolumeUnitSerializer(serializers.ModelSerializer):
    """Serializer for VolumeUnit model."""
    
    class Meta:
        model = VolumeUnit
        fields = ['id', 'name', 'abbreviation', 'sort_order']


class MetadataSerializer(serializers.Serializer):
    """Combined serializer for all metadata."""
    
    cargo_types = CargoTypeSerializer(many=True, read_only=True)
    transport_types = TransportTypeSerializer(many=True, read_only=True)
    volume_units = VolumeUnitSerializer(many=True, read_only=True)
    currencies = CurrencySerializer(many=True, read_only=True)


class ShipmentListSerializer(serializers.ModelSerializer):
    """Serializer for Shipment list view."""
    
    cargo_type = CargoTypeSerializer(read_only=True)
    volume_unit = VolumeUnitSerializer(read_only=True)
    transport_type = TransportTypeSerializer(read_only=True)
    preferred_currency = CurrencySerializer(read_only=True)
    bids_count = serializers.IntegerField(read_only=True)
    
    customer_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Shipment
        fields = [
            'id',
            'display_id',
            'pickup_location',
            'pickup_date',
            'delivery_location',
            'cargo_type',
            'cargo_volume',
            'volume_unit',
            'transport_type',
            'preferred_currency',
            'additional_conditions',
            'status',
            'created_at',
            'bids_count',
            'customer_info'
        ]
    
    def get_customer_info(self, obj):
        """Return customer information."""
        return {
            'name': obj.user.get_full_name(),
            'company': obj.user.company_name or '',
            'email': obj.user.email,
            'phone': obj.user.mobile
        }


class ShipmentDetailSerializer(ShipmentListSerializer):
    """Serializer for Shipment detail view (includes all info)."""
    
    class Meta(ShipmentListSerializer.Meta):
        fields = ShipmentListSerializer.Meta.fields


class BidCreateSerializer(serializers.Serializer):
    """Serializer for creating a bid."""
    
    company_name = serializers.CharField(
        max_length=200,
        help_text='Name of the company submitting the bid'
    )
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        help_text='Bid price (must be positive)'
    )
    currency = serializers.CharField(
        max_length=3,
        help_text='Currency code (must match shipment preferred currency)'
    )
    estimated_delivery_time = serializers.IntegerField(
        min_value=1,
        help_text='Estimated delivery time in hours'
    )
    comment = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text='Additional comments (optional)'
    )
    contact_person = serializers.CharField(
        max_length=100,
        help_text='Contact person name'
    )
    contact_phone = serializers.CharField(
        max_length=20,
        help_text='Contact phone number'
    )
    driver_id = serializers.CharField(
        max_length=100,
        required=True,
        help_text='Unique ID of the driver on your platform'
    )
    
    def validate_currency(self, value):
        """Validate that currency exists."""
        try:
            Currency.objects.get(code=value, is_active=True)
        except Currency.DoesNotExist:
            raise serializers.ValidationError('Invalid currency code')
        return value
    
    def validate(self, data):
        """Validate bid data against shipment."""
        # Get shipment from context
        shipment = self.context.get('shipment')
        if not shipment:
            raise serializers.ValidationError('Shipment not found')
        
        # Get currency object
        try:
            currency = Currency.objects.get(code=data['currency'])
        except Currency.DoesNotExist:
            raise serializers.ValidationError({'currency': 'Invalid currency code'})
        
        # Check if currency matches shipment's preferred currency
        if currency.id != shipment.preferred_currency_id:
            raise serializers.ValidationError({
                'currency': 'Currency must match shipment preferred currency'
            })
        
        # Store currency object for later use
        data['currency_obj'] = currency
        
        return data


class BidResponseSerializer(serializers.ModelSerializer):
    """Serializer for bid response."""
    
    currency = CurrencySerializer(read_only=True)
    
    class Meta:
        model = Bid
        fields = [
            'id',
            'display_id',
            'shipment_id',
            'company_name',
            'price',
            'currency',
            'estimated_delivery_time',
            'comment',
            'contact_person',
            'contact_phone',
            'status',
            'created_at'
        ]
        read_only_fields = ['id', 'shipment_id', 'status', 'created_at']
