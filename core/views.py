from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from users.models import UserRole
from django.conf import settings
from datetime import date, timedelta
import requests
import threading
from .models import ExchangeRate, Currency
from inventory.views import sync_daily_stock

def run_maintenance_tasks():
    update_exchange_rates()
    sync_daily_stock()


@login_required
def dashboard_view(request):

    threading.Thread(target=run_maintenance_tasks, daemon=True).start()
    
    user_roles = UserRole.objects.filter(user_id=request.user)

    permissions = {

        'customers':0,
        'suppliers':0,
        'materials':0,
        'purchases':0,
        'sales':0,
        'inventory':0,
        'accounting':0,
        'reporting':0,
    }

    for user_role in user_roles:
        role = user_role.role
        for module in permissions.keys():
            current_permission = getattr(role, module)
            if current_permission > permissions[module]:
                permissions[module] = current_permission


    context = {

        'user': request.user,
        'permissions': permissions,
        'roles': [ur.role.role_name for ur in user_roles],

    }

    return render(request, 'core/dashboard.html', context)



def update_exchange_rates():
    try:
        base_currency_code = getattr(settings, 'BASE_CURRENCY', 'USD')
        today = date.today()
        currencies_in_erp = {c.code: c for c in Currency.objects.all()}

        # Obtener la última fecha registrada (ordenada por fecha descendente)
        last_rate = ExchangeRate.objects.order_by('-date').first()
        if not last_rate:
            start_date = today - timedelta(days=1)
        else:
            start_date = last_rate.date + timedelta(days=1)
            if start_date > today:
                return  # Ya actualizado

        # Construir URL según si es una fecha única o un rango
        if start_date == today:
            url = f"https://api.frankfurter.dev/v1/{start_date.isoformat()}?base={base_currency_code}"
        else:
            url = f"https://api.frankfurter.dev/v1/{start_date.isoformat()}..{today.isoformat()}?base={base_currency_code}"

        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return

        data = response.json()
        rates_data = data.get('rates', {})
        if not rates_data:
            return

        # Detectar si es un rango (los valores de rates_data son diccionarios)
        first_value = next(iter(rates_data.values()), None)
        is_range = isinstance(first_value, dict)

        if is_range:
            # Para cada fecha en el rango
            for date_str, rates in rates_data.items():
                # Actualizar cada moneda para esta fecha
                for code, rate_value in rates.items():
                    if code in currencies_in_erp:
                        ExchangeRate.objects.update_or_create(
                            currency=currencies_in_erp[code],
                            date=date_str,
                            defaults={'rate': rate_value}
                        )
                # Actualizar la moneda base para esta fecha (si existe en ERP)
                if base_currency_code in currencies_in_erp:
                    ExchangeRate.objects.update_or_create(
                        currency=currencies_in_erp[base_currency_code],
                        date=date_str,
                        defaults={'rate': 1.0}
                    )
        else:
            # Fecha única
            target_date = data.get('date')
            if not target_date:
                return
            for code, rate_value in rates_data.items():
                if code in currencies_in_erp:
                    ExchangeRate.objects.update_or_create(
                        currency=currencies_in_erp[code],
                        date=target_date,
                        defaults={'rate': rate_value}
                    )
            if base_currency_code in currencies_in_erp:
                ExchangeRate.objects.update_or_create(
                    currency=currencies_in_erp[base_currency_code],
                    date=target_date,
                    defaults={'rate': 1.0}
                )

    except Exception as e:
        # En producción, usa logging en lugar de print
        print(f"Error updating exchange rates: {e}")