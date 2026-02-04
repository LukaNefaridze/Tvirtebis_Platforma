from django.urls import path
from .views import (
    MetadataAPIView,
    ShipmentListAPIView,
    ShipmentDetailAPIView,
    BidCreateAPIView,
    PlatformBidListAPIView
)


app_name = 'api_v1'

urlpatterns = [
    path('metadata/', MetadataAPIView.as_view(), name='metadata'),
    path('shipments/', ShipmentListAPIView.as_view(), name='shipment-list'),
    path('shipments/<uuid:pk>/', ShipmentDetailAPIView.as_view(), name='shipment-detail'),
    path('shipments/<uuid:pk>/bids/', BidCreateAPIView.as_view(), name='bid-create'),
    path('my-bids/', PlatformBidListAPIView.as_view(), name='my-bids'),
]
