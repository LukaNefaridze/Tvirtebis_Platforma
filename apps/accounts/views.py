from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, logout
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from .models import User, AdminUser
from .utils import validate_password_strength


def login_router(request):
    """
    Route authenticated users to appropriate location after login.
    Both AdminUsers and regular Users are now directed to the admin panel,
    with different navigation and permissions based on user type.
    """
    if not request.user.is_authenticated:
        return redirect('admin:login')
    
    if isinstance(request.user, AdminUser):
        return redirect('admin:index')
    elif isinstance(request.user, User):
        if request.user.must_change_password:
            return redirect('accounts:password_change')
        # Redirect regular users to user portal
        return redirect('accounts:shipments')
    
    return redirect('admin:login')


@login_required(login_url='/admin/login/')
def user_shipments(request):
    """
    List shipments for regular users.
    """
    # Redirect AdminUsers to Django admin
    if isinstance(request.user, AdminUser):
        return redirect('admin:shipments_shipment_changelist')
    
    if not isinstance(request.user, User):
        return redirect('admin:login')
    
    # Check password change requirement
    if request.user.must_change_password:
        return redirect('accounts:password_change')
    
    # Get user's shipments
    shipments = request.user.shipments.select_related(
        'cargo_type', 'transport_type', 'volume_unit', 'preferred_currency'
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(shipments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'user': request.user,
        'shipments': page_obj,
        'total_count': shipments.count(),
    }
    return render(request, 'accounts/shipments_list.html', context)


@login_required(login_url='/admin/login/')
def user_shipment_detail(request, pk):
    """
    View shipment details for regular users.
    """
    if isinstance(request.user, AdminUser):
        return redirect('admin:shipments_shipment_change', pk)
    
    if not isinstance(request.user, User):
        return redirect('admin:login')
    
    if request.user.must_change_password:
        return redirect('accounts:password_change')
    
    shipment = get_object_or_404(
        request.user.shipments.select_related(
            'cargo_type', 'transport_type', 'volume_unit', 'preferred_currency', 'selected_bid'
        ).prefetch_related('bids__broker', 'bids__currency'),
        pk=pk
    )
    
    context = {
        'user': request.user,
        'shipment': shipment,
        'bids': shipment.bids.select_related('broker', 'currency').all().order_by('price'),  # Order by price (cheapest first)
    }
    return render(request, 'accounts/shipment_detail.html', context)


@login_required(login_url='/admin/login/')
def accept_bid(request, shipment_pk, bid_pk):
    """Accept a bid for a shipment."""
    if request.method != 'POST':
        messages.error(request, _('არასწორი მოთხოვნა'))
        return redirect('accounts:shipment_detail', pk=shipment_pk)
    
    if not isinstance(request.user, User):
        return redirect('admin:login')
    
    shipment = get_object_or_404(request.user.shipments, pk=shipment_pk)
    bid = get_object_or_404(shipment.bids, pk=bid_pk)
    
    try:
        shipment.mark_completed(bid)
        messages.success(request, _('ბიდი წარმატებით მიიღეთ. განაცხადი დასრულებულია.'))
    except ValueError as e:
        messages.error(request, str(e))
    
    return redirect('accounts:shipment_detail', pk=shipment_pk)


@login_required(login_url='/admin/login/')
def reject_bid(request, shipment_pk, bid_pk):
    """Reject a bid for a shipment."""
    if request.method != 'POST':
        messages.error(request, _('არასწორი მოთხოვნა'))
        return redirect('accounts:shipment_detail', pk=shipment_pk)
    
    if not isinstance(request.user, User):
        return redirect('admin:login')
    
    shipment = get_object_or_404(request.user.shipments, pk=shipment_pk)
    bid = get_object_or_404(shipment.bids, pk=bid_pk)
    
    try:
        bid.reject()
        messages.success(request, _('ბიდი უარყოფილია.'))
    except Exception as e:
        messages.error(request, str(e))
    
    return redirect('accounts:shipment_detail', pk=shipment_pk)


@login_required(login_url='/admin/login/')
def user_bids_history(request):
    """
    List all bids for the user's shipments (historical view).
    """
    if isinstance(request.user, AdminUser):
        return redirect('admin:bids_bid_changelist')
    
    if not isinstance(request.user, User):
        return redirect('admin:login')
    
    # Get all bids for user's shipments
    from apps.bids.models import Bid
    
    bids = Bid.objects.filter(
        shipment__user=request.user
    ).select_related(
        'shipment', 'currency', 'broker'
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(bids, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'user': request.user,
        'bids': page_obj,
        'total_count': bids.count(),
    }
    return render(request, 'accounts/bids_history.html', context)


@login_required(login_url='/admin/login/')
def user_password_change(request):
    """
    Custom password change view for regular User model.
    """
    # Redirect AdminUsers to Django admin password change
    if isinstance(request.user, AdminUser):
        return redirect('admin:password_change')
    
    if not isinstance(request.user, User):
        return redirect('admin:login')
    
    if request.method == 'POST':
        old_password = request.POST.get('old_password', '')
        new_password1 = request.POST.get('new_password1', '')
        new_password2 = request.POST.get('new_password2', '')
        
        errors = []
        
        # Validate old password
        if not request.user.check_password(old_password):
            errors.append(_('ძველი პაროლი არასწორია.'))
        
        # Validate new passwords match
        if new_password1 != new_password2:
            errors.append(_('ახალი პაროლები არ ემთხვევა.'))
        
        # Validate password strength
        if new_password1:
            try:
                validate_password_strength(new_password1)
            except ValidationError as e:
                errors.append(str(e.message))
        
        # Check new password is different from old
        if old_password and new_password1 and old_password == new_password1:
            errors.append(_('ახალი პაროლი განსხვავებული უნდა იყოს ძველისგან.'))
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Change password
            request.user.set_password(new_password1)
            request.user.must_change_password = False
            request.user.save(update_fields=['password', 'must_change_password'])
            
            # Keep user logged in
            update_session_auth_hash(request, request.user)
            
            messages.success(request, _('პაროლი წარმატებით შეიცვალა!'))
            return redirect('accounts:shipments')
    
    context = {
        'title': _('პაროლის შეცვლა'),
        'user': request.user,
    }
    return render(request, 'accounts/password_change.html', context)


@login_required(login_url='/admin/login/')
def user_logout(request):
    """Log out the user and redirect to login page."""
    logout(request)
    messages.success(request, _('თქვენ წარმატებით გამოხვედით სისტემიდან.'))
    return redirect('admin:login')
