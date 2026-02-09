from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
# from django_ratelimit.decorators import ratelimit
# from django.utils.decorators import method_decorator
from apps.metadata.models import Currency, CargoType, TransportType, VolumeUnit
from apps.shipments.models import Shipment
from apps.bids.models import Bid
from .serializers import (
    MetadataSerializer,
    ShipmentListSerializer,
    ShipmentDetailSerializer,
    BidCreateSerializer,
    BidResponseSerializer
)
from .permissions import IsAuthenticatedPlatform
from ..utils import success_response, error_response


class MetadataAPIView(APIView):
    """
    GET /api/v1/metadata/
    
    Returns all active metadata (cargo types, transport types, volume units, currencies).
    No authentication required.
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Return all active metadata."""
        data = {
            'cargo_types': CargoType.active.all(),
            'transport_types': TransportType.active.all(),
            'volume_units': VolumeUnit.active.all(),
            'currencies': Currency.active.all()
        }
        
        serializer = MetadataSerializer(data)
        return success_response(serializer.data)


# @method_decorator(ratelimit(key='user', rate='100/h', method='GET'), name='dispatch')
class ShipmentListAPIView(generics.ListAPIView):
    """
    GET /api/v1/shipments/
    
    Returns paginated list of shipments.
    Requires platform authentication.
    
    Query parameters:
    - status: active (default), completed, cancelled
    - date_from: YYYY-MM-DD
    - date_to: YYYY-MM-DD
    - pickup_location: location name
    - delivery_location: location name
    - transport_type_id: UUID
    - cargo_type_id: UUID
    - currency: currency code
    - page: page number (default: 1)
    - limit: items per page (default: 20, max: 100)
    """
    
    serializer_class = ShipmentListSerializer
    permission_classes = [IsAuthenticatedPlatform]
    
    def get_queryset(self):
        """Return filtered queryset based on query parameters."""
        queryset = Shipment.objects.select_related(
            'user', 'cargo_type', 'volume_unit', 'transport_type', 'preferred_currency'
        ).annotate(
            bids_count=Count('bids')
        )
        
        # Exclude shipments from soft-deleted users
        queryset = queryset.filter(user__is_deleted=False)
        
        # Filter by status (default: active)
        status_filter = self.request.query_params.get('status', 'active')
        if status_filter in ['active', 'completed', 'cancelled']:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(pickup_date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(pickup_date__lte=date_to)
        
        # Filter by locations (partial match)
        pickup_location = self.request.query_params.get('pickup_location')
        if pickup_location:
            queryset = queryset.filter(pickup_location__icontains=pickup_location)
        
        delivery_location = self.request.query_params.get('delivery_location')
        if delivery_location:
            queryset = queryset.filter(delivery_location__icontains=delivery_location)
        
        # Filter by transport type
        transport_type_id = self.request.query_params.get('transport_type_id')
        if transport_type_id:
            queryset = queryset.filter(transport_type_id=transport_type_id)
        
        # Filter by cargo type
        cargo_type_id = self.request.query_params.get('cargo_type_id')
        if cargo_type_id:
            queryset = queryset.filter(cargo_type_id=cargo_type_id)
        
        # Filter by currency
        currency = self.request.query_params.get('currency')
        if currency:
            queryset = queryset.filter(preferred_currency__code=currency)
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """Override list to return custom response format."""
        queryset = self.get_queryset()
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            pagination_data = self.paginator.get_paginated_response(serializer.data).data
            
            return success_response({
                'shipments': serializer.data,
                'pagination': {
                    'current_page': pagination_data.get('current', 1),
                    'total_pages': pagination_data.get('num_pages', 1),
                    'total_items': pagination_data.get('count', 0),
                    'items_per_page': self.paginator.page_size
                }
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response({'shipments': serializer.data})


# @method_decorator(ratelimit(key='user', rate='200/h', method='GET'), name='dispatch')
class ShipmentDetailAPIView(generics.RetrieveAPIView):
    """
    GET /api/v1/shipments/{id}/
    
    Returns detailed information about a specific shipment.
    Requires platform authentication.
    """
    
    serializer_class = ShipmentDetailSerializer
    permission_classes = [IsAuthenticatedPlatform]
    lookup_field = 'pk'
    
    def get_queryset(self):
        """Return queryset with related objects, excluding soft-deleted users."""
        return Shipment.objects.select_related(
            'user', 'cargo_type', 'volume_unit', 'transport_type', 'preferred_currency'
        ).filter(
            user__is_deleted=False
        ).annotate(
            bids_count=Count('bids')
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to return custom response format."""
        try:
            instance = self.get_object()
        except Shipment.DoesNotExist:
            return error_response(
                'SHIPMENT_NOT_FOUND',
                'Shipment not found',
                status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)


# @method_decorator(ratelimit(key='user', rate='50/h', method='POST'), name='dispatch')
class BidCreateAPIView(APIView):
    """
    POST /api/v1/shipments/{id}/bids/
    
    Submit a bid on a shipment.
    Requires platform authentication.
    
    Request body:
    {
        "company_name": "string",
        "price": decimal,
        "currency": "string",
        "estimated_delivery_time": integer,
        "comment": "string" (optional),
        "contact_person": "string",
        "contact_phone": "string",
        "driver_id": "string"
    }
    """
    
    permission_classes = [IsAuthenticatedPlatform]
    
    def post(self, request, pk):
        """Create a new bid on a shipment."""
        # Get shipment (exclude shipments from soft-deleted users)
        shipment = get_object_or_404(Shipment, pk=pk, user__is_deleted=False)
        
        # Validate request data
        serializer = BidCreateSerializer(
            data=request.data,
            context={'shipment': shipment}
        )
        
        if not serializer.is_valid():
            return error_response(
                'VALIDATION_ERROR',
                serializer.errors,
                status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        currency = validated_data.pop('currency_obj')
        platform = request.user  # Platform instance from authentication
        
        # Check if bid can be submitted
        can_submit, error_code, error_message = Bid.objects.can_submit_bid(
            shipment=shipment,
            platform=platform,
            price=validated_data['price'],
            estimated_delivery_time=validated_data['estimated_delivery_time'],
            currency=currency,
            company_name=validated_data['company_name'],
            external_user_id=validated_data['driver_id']
        )
        
        if not can_submit:
            return error_response(
                error_code,
                error_message,
                status.HTTP_409_CONFLICT
            )
        
        # Create bid
        bid = Bid.objects.create(
            shipment=shipment,
            platform=platform,
            company_name=validated_data['company_name'],
            price=validated_data['price'],
            currency=currency,
            estimated_delivery_time=validated_data['estimated_delivery_time'],
            comment=validated_data.get('comment', ''),
            contact_person=validated_data['contact_person'],
            contact_phone=validated_data['contact_phone'],
            external_user_id=validated_data['driver_id'],
            status='pending'
        )
        
        # Return success response
        response_serializer = BidResponseSerializer(bid)
        return Response({
            'success': True,
            'message': 'Bid submitted successfully',
            'data': {
                'bid_id': str(bid.id),
                'shipment_id': str(shipment.id),
                'status': bid.status,
                'created_at': bid.created_at.isoformat()
            }
        }, status=status.HTTP_201_CREATED)


class PlatformBidListAPIView(generics.ListAPIView):
    """
    GET /api/v1/my-bids/
    
    Returns list of bids submitted by the authenticated platform.
    Requires platform authentication.
    """
    serializer_class = BidResponseSerializer
    permission_classes = [IsAuthenticatedPlatform]
    
    def get_queryset(self):
        """Return bids for the current platform."""
        return Bid.objects.filter(platform=self.request.user).select_related(
            'shipment', 'currency'
        ).order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """Override list to return custom response format."""
        queryset = self.get_queryset()
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            pagination_data = self.paginator.get_paginated_response(serializer.data).data
            
            return success_response({
                'bids': serializer.data,
                'pagination': {
                    'current_page': pagination_data.get('current', 1),
                    'total_pages': pagination_data.get('num_pages', 1),
                    'total_items': pagination_data.get('count', 0),
                    'items_per_page': self.paginator.page_size
                }
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response({'bids': serializer.data})
