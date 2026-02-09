from django.shortcuts import redirect
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from .forms import CustomPasswordChangeForm

def login_router(request):
    """
    Route authenticated users to appropriate location after login.
    All users are directed to the admin panel.
    """
    if not request.user.is_authenticated:
        return redirect('admin:login')
    
    return redirect('admin:index')

class CustomPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm
    success_url = reverse_lazy('admin:index')
    template_name = 'registration/password_change_form.html'

    def form_valid(self, form):
        # Update the user's flag
        user = form.user
        if user.must_change_password:
            user.must_change_password = False
            user.save(update_fields=['must_change_password'])
        
        messages.success(self.request, _('პაროლი წარმატებით შეიცვალა.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add admin site context for Unfold/Admin templates
        context.update(admin.site.each_context(self.request))
        return context
