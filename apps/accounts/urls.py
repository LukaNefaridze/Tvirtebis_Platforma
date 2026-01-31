from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.login_router, name='login_router'),
    path('shipments/', views.user_shipments, name='shipments'),
    path('shipments/<uuid:pk>/', views.user_shipment_detail, name='shipment_detail'),
    path('shipments/<uuid:shipment_pk>/accept-bid/<uuid:bid_pk>/', views.accept_bid, name='accept_bid'),
    path('shipments/<uuid:shipment_pk>/reject-bid/<uuid:bid_pk>/', views.reject_bid, name='reject_bid'),
    path('bids/', views.user_bids_history, name='bids_history'),
    path('password-change/', views.user_password_change, name='password_change'),
    path('logout/', views.user_logout, name='logout'),
]
