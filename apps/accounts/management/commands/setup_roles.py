
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.shipments.models import Shipment
from apps.bids.models import Bid
from apps.metadata.models import CargoType, TransportType, VolumeUnit, Currency

class Command(BaseCommand):
    help = 'Sets up the Client group with default permissions'

    def handle(self, *args, **options):
        client_group, created = Group.objects.get_or_create(name='Client')

        # 1. Define models user can EDIT (Metadata)
        metadata_models = [CargoType, TransportType, VolumeUnit, Currency]
        for model in metadata_models:
            ct = ContentType.objects.get_for_model(model)
            permissions = Permission.objects.filter(content_type=ct, codename__startswith='change_')
            client_group.permissions.add(*permissions)
            self.stdout.write(f'Added change permissions for {model.__name__}')

        # 2. Define Shipment Permissions (Add, View, Change)
        # Note: We give 'change' permission so they can access the edit page to perform actions (Accept/Reject),
        # but we will lock the fields in admin.py.
        shipment_ct = ContentType.objects.get_for_model(Shipment)
        shipment_perms = Permission.objects.filter(
            content_type=shipment_ct, 
            codename__in=['add_shipment', 'view_shipment', 'change_shipment']
        )
        client_group.permissions.add(*shipment_perms)
        self.stdout.write('Added Shipment permissions (add, view, change)')

        # 3. Define Bid Permissions (View only)
        # Actions like "Accept" are handled via Shipment methods, not direct Bid editing.
        bid_ct = ContentType.objects.get_for_model(Bid)
        bid_perms = Permission.objects.filter(
            content_type=bid_ct, 
            codename__in=['view_bid']
        )
        client_group.permissions.add(*bid_perms)
        self.stdout.write('Added Bid permissions (view)')

        self.stdout.write(self.style.SUCCESS('Client group configured successfully'))
