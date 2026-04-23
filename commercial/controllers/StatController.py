# views.py
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.db.models import Count
from django.utils import timezone
# from django.contrib.auth.decorators import login_required

from authentification.decoratos import admin_required
from authentification.decoratos import user_required
from authentification.metier.User import User
from commercial.metier.CommercialProposal import CommercialProposal


def _parse_requested_year(request):
    raw_year = str(request.GET.get("year", "")).strip()
    if raw_year == "":
        return timezone.localdate().year

    try:
        year = int(raw_year)
    except (TypeError, ValueError):
        return None

    return year


def _build_stat_by_commercial(year):
    month_labels = [
        "Janvier",
        "Février",
        "Mars",
        "Avril",
        "Mai",
        "Juin",
        "Juillet",
        "Août",
        "Septembre",
        "Octobre",
        "Novembre",
        "Décembre",
    ]
    commercial_users = User.objects.all()
    proposal_counts = {
        row["commercial_id"]: row["total"]
        for row in (
            CommercialProposal.objects.filter(date_proposal__year=year)
            .values("commercial_id")
            .annotate(total=Count("id"))
        )
    }

    proposal_margins = {commercial.id: {month: 0.0 for month in range(1, 13)} for commercial in commercial_users}

    proposals = (
        CommercialProposal.objects.filter(date_proposal__year=year)
        .prefetch_related("proposal_products")
    )

    for proposal in proposals:
        commercial_id = proposal.commercial_id
        month_number = proposal.date_proposal.month
        margin = 0.0

        for proposal_product in proposal.proposal_products.all():
            quantity = max(0.0, float(proposal_product.quantity or 0))
            sale_unit_price = max(0.0, float(proposal_product.sale_unit_price or 0))
            purchase_unit_price = max(0.0, float(proposal_product.purchase_unit_price or 0))
            margin += (sale_unit_price * quantity) - (purchase_unit_price * quantity)

        if commercial_id in proposal_margins:
            proposal_margins[commercial_id][month_number] += margin

    stat_by_commercial = []
    for commercial in commercial_users:
        monthly_profit = [
            {
                "month": month_labels[month_number - 1],
                "value": round(proposal_margins.get(commercial.id, {}).get(month_number, 0.0), 2),
            }
            for month_number in range(1, 13)
        ]

        yearly_profit = round(
            sum(item["value"] for item in monthly_profit),
            2,
        )

        stat_by_commercial.append(
            {
                "id": commercial.id,
                "name": f"{commercial.first_name} {commercial.last_name}".strip(),
                "proposals": proposal_counts.get(commercial.id, 0),
                "yearlyProfit": yearly_profit,
                "monthlyProfit": monthly_profit,
            }
        )

    return stat_by_commercial


def _build_profit_by_month(year):
    month_labels = [
        "Janvier",
        "Février",
        "Mars",
        "Avril",
        "Mai",
        "Juin",
        "Juillet",
        "Août",
        "Septembre",
        "Octobre",
        "Novembre",
        "Décembre",
    ]
    profit_by_month = {month_number: 0.0 for month_number in range(1, 13)}

    proposals = (
        CommercialProposal.objects.filter(date_proposal__year=year)
        .prefetch_related("proposal_products")
    )

    for proposal in proposals:
        month_number = proposal.date_proposal.month
        monthly_profit = 0.0

        for proposal_product in proposal.proposal_products.all():
            quantity = max(0.0, float(proposal_product.quantity or 0))
            sale_unit_price = max(0.0, float(proposal_product.sale_unit_price or 0))
            purchase_unit_price = max(0.0, float(proposal_product.purchase_unit_price or 0))
            monthly_profit += (sale_unit_price * quantity) - (purchase_unit_price * quantity)

        profit_by_month[month_number] += monthly_profit

    return [
        {
            "month": month_labels[month_number - 1],
            "value": round(profit_by_month[month_number], 2),
        }
        for month_number in range(1, 13)
    ]


def _build_profit_by_month_for_commercial(year, commercial_user):
    month_labels = [
        "Janvier",
        "Février",
        "Mars",
        "Avril",
        "Mai",
        "Juin",
        "Juillet",
        "Août",
        "Septembre",
        "Octobre",
        "Novembre",
        "Décembre",
    ]
    profit_by_month = {month_number: 0.0 for month_number in range(1, 13)}

    proposals = (
        CommercialProposal.objects.filter(state=1, date_proposal__year=year, commercial=commercial_user)
        .prefetch_related("proposal_products")
    )

    for proposal in proposals:
        month_number = proposal.date_proposal.month
        monthly_profit = 0.0

        for proposal_product in proposal.proposal_products.all():
            quantity = max(0.0, float(proposal_product.quantity or 0))
            sale_unit_price = max(0.0, float(proposal_product.sale_unit_price or 0))
            purchase_unit_price = max(0.0, float(proposal_product.purchase_unit_price or 0))
            monthly_profit += (sale_unit_price * quantity) - (purchase_unit_price * quantity)

        profit_by_month[month_number] += monthly_profit

    return [
        {
            "month": month_labels[month_number - 1],
            "value": round(profit_by_month[month_number], 2),
        }
        for month_number in range(1, 13)
    ]


def _build_user_dashboard_counts(commercial_user):
    proposals = CommercialProposal.objects.filter(commercial=commercial_user)
    total_created = proposals.count()
    total_validated = proposals.filter(state=1).count()
    total_pending = proposals.filter(state=0).count()

    return {
        "created": total_created,
        "validated": total_validated,
        "pending": total_pending,
    }

@require_GET
@admin_required
def dashboard_page(request):
    print(request.user.first_name)
    return render(request, "views/dashboard.html")

@require_GET
@admin_required
def admin_page(request):
    return render(request, "views/admin.html")

@require_GET
@admin_required
def get_initial_dashboard_data(request):
    current_year = timezone.localdate().year
    data = {
        "year": current_year,
        "statByCommercial": _build_stat_by_commercial(current_year),
        "profitByMonth": _build_profit_by_month(current_year),
    }
    return JsonResponse(data)


@require_GET
@admin_required
def get_stat_by_commercial(request):
    requested_year = _parse_requested_year(request)
    if requested_year is None:
        return JsonResponse({"error": "Parametre year invalide."}, status=400)

    data = {
        "year": requested_year,
        "statByCommercial": _build_stat_by_commercial(requested_year),
    }
    return JsonResponse(data)


@require_GET
@admin_required
def get_profit_by_month(request):
    requested_year = _parse_requested_year(request)
    if requested_year is None:
        return JsonResponse({"error": "Parametre year invalide."}, status=400)

    data = {
        "year": requested_year,
        "profitByMonth": _build_profit_by_month(requested_year),
    }
    return JsonResponse(data)


@require_GET
@user_required
def user_dashboard_page(request):
    return render(request, "views/dashboard_user.html")


@require_GET
@user_required
def get_initial_user_dashboard_data(request):
    current_year = timezone.localdate().year
    data = {
        "year": current_year,
        "counts": _build_user_dashboard_counts(request.user),
        "profitByMonth": _build_profit_by_month_for_commercial(current_year, request.user),
    }
    return JsonResponse(data)


@require_GET
@user_required
def get_user_profit_by_month(request):
    requested_year = _parse_requested_year(request)
    if requested_year is None:
        return JsonResponse({"error": "Parametre year invalide."}, status=400)

    data = {
        "year": requested_year,
        "profitByMonth": _build_profit_by_month_for_commercial(requested_year, request.user),
    }
    return JsonResponse(data)