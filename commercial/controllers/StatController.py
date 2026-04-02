# views.py
from django.shortcuts import render
from django.views.decorators.http import require_GET
# from django.contrib.auth.decorators import login_required

from authentification.decoratos import admin_required

@require_GET
@admin_required
def dashboard_page(request):
    return render(request, "views/dashboard.html")

@require_GET
@admin_required
def admin_page(request):
    return render(request, "views/admin.html")