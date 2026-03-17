# views.py
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required

@require_GET
@login_required(login_url='login_user_page')
def dashboard_page(request):
    return render(request, "views/dashboard.html")