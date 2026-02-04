from django.shortcuts import redirect

def login_router(request):
    """
    Route authenticated users to appropriate location after login.
    All users are directed to the admin panel.
    """
    if not request.user.is_authenticated:
        return redirect('admin:login')
    
    return redirect('admin:index')
