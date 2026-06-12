import json
from django.core.serializers.json import DjangoJSONEncoder
import csv
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.db import transaction, models
from django.core.paginator import Paginator
from .models import PurchaseOrder, LinesPurchaseOrder, OrderStatus
from suppliers.models import Supplier
from materials.models import Material, Unit
from core.models import Currency
from users.models import UserRole

# ------------------------------------------------------------
# Listado de órdenes de compra
# ------------------------------------------------------------
@login_required
def purchase_order_list(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__purchases')
    )['max_perm'] or 0
    if max_permission == 0:
        return redirect('dashboard')

    purchase_orders = PurchaseOrder.objects.select_related('id_supplier', 'order_status', 'created_by').all().order_by('id_purchase_order','-issue_date')

    id_po = request.GET.get('id_purchase_order')
    supplier_id = request.GET.get('supplier_id')
    status_symbol = request.GET.get('status_symbol')

    if id_po:
        purchase_orders = purchase_orders.filter(id_purchase_order__icontains=id_po)
    if supplier_id:
        purchase_orders = purchase_orders.filter(id_supplier__id_supplier__icontains=supplier_id)
    if status_symbol:
        purchase_orders = purchase_orders.filter(order_status__symbol__iexact=status_symbol)

    if request.GET.get('export') == 'csv':
        return export_purchase_orders_csv(purchase_orders)

    paginator = Paginator(purchase_orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'permissions': {'purchases': max_permission},
        'statuses': OrderStatus.objects.all().order_by('name'),
    }
    return render(request, 'purchases/purchase_order_list.html', context)

def export_purchase_orders_csv(queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="purchase_orders.csv"'
    response.write('\ufeff'.encode('utf-8'))
    writer = csv.writer(response)
    writer.writerow([
        'ID Purchase Order', 'Supplier ID', 'Supplier Name', 'Issue Date',
        'Estimated Delivery Date', 'Status Symbol', 'Status Name',
        'Created By', 'Created At'
    ])
    for po in queryset:
        writer.writerow([
            po.id_purchase_order,
            po.id_supplier.id_supplier,
            po.id_supplier.name,
            po.issue_date.strftime('%Y-%m-%d %H:%M:%S'),
            po.estimated_delivery_date.strftime('%Y-%m-%d') if po.estimated_delivery_date else '',
            po.order_status.symbol,
            po.order_status.name,
            po.created_by.username if po.created_by else 'N/A',
            po.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    return response

# ------------------------------------------------------------
# API: Detalles de proveedor (para AJAX)
# ------------------------------------------------------------
def get_supplier_details(request, supplier_id):
    supplier = get_object_or_404(Supplier, id_supplier=supplier_id)
    data = {
        'id_supplier': supplier.id_supplier,
        'name': supplier.name,
        'legal_name': supplier.legal_name,
        'tax_id': supplier.tax_id,
        'address': supplier.address,
        'city': supplier.city,
        'state_province': supplier.state_province,
        'country': supplier.country.name if supplier.country else '',
        'zip_code': supplier.zip_code,
        'phone': supplier.phone,
        'email': supplier.email,
        'contact_name': supplier.contact_name,
        'payment_terms': supplier.payment_terms.name if supplier.payment_terms else '',
        'payment_method': supplier.payment_method.name if supplier.payment_method else '',
        'currency': supplier.currency.code if supplier.currency else 'USD',
    }
    return JsonResponse(data)

def get_material_details(request, material_id):
    material = get_object_or_404(Material, id_material=material_id)
    data = {
        'id_material': material.id_material,
        'unit': material.unit.symbol if material.unit else '',
        'description': material.description,
    }
    return JsonResponse(data)

# ------------------------------------------------------------
# Formulario de creación / edición (reutiliza misma plantilla)
# ------------------------------------------------------------
@login_required
def purchase_order_form(request, pk=None):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__purchases')
    )['max_perm'] or 0
    if max_permission == 0:
        return redirect('dashboard')
    if max_permission == 1:
        return redirect('purchases:purchase_order_list')

    purchase_order = None
    lines = []
    purchase_order_json = None
    lines_json = None

    if pk:
        purchase_order = get_object_or_404(PurchaseOrder, pk=pk)
        # Usar el relacionador correcto: 'lines_purchase_order'
        lines = purchase_order.lines_purchase_order.all().order_by('position')
        if max_permission < 2:
            return redirect('purchases:purchase_order_list')

        # Preparar datos serializables para JSON
        po_data = {
            'id_purchase_order': purchase_order.id_purchase_order,
            'estimated_delivery_date': purchase_order.estimated_delivery_date.strftime('%Y-%m-%d') if purchase_order.estimated_delivery_date else None,
            'id_supplier': {
                'id_supplier': purchase_order.id_supplier.id_supplier,
                'name': purchase_order.id_supplier.name,
            }
        }
        lines_data = []
        for line in lines:
            lines_data.append({
                'id_material': {
                    'id_material': line.id_material.id_material,
                    'description': line.id_material.description,
                },
                'quantity': line.quantity,
                'unit_material': {
                    'symbol': line.unit_material.symbol,
                },
                'price': line.price,
                'currency_supplier': {
                    'code': line.currency_supplier.code,
                },
            })
        purchase_order_json = json.dumps(po_data, cls=DjangoJSONEncoder)
        lines_json = json.dumps(lines_data, cls=DjangoJSONEncoder)

    context = {
        'title': 'Edit Purchase Order' if purchase_order else 'Create New Purchase Order',
        'purchase_order': purchase_order,
        'lines': lines,
        'purchase_order_json': purchase_order_json,
        'lines_json': lines_json,
    }
    return render(request, 'purchases/purchase_order_form.html', context)

# ------------------------------------------------------------
# Crear orden de compra (vía AJAX POST)
# ------------------------------------------------------------
@csrf_exempt
@require_POST
@transaction.atomic
def create_purchase_order(request):
    try:
        data = json.loads(request.body)

        supplier_id_str = data.get('id_supplier')
        estimated_delivery_date_str = data.get('estimated_delivery_date')
        lines_data = data.get('lines', [])
        edit_mode = data.get('edit_mode', False)
        po_id = data.get('id_purchase_order')  # solo en modo edición

        if not supplier_id_str or not estimated_delivery_date_str or not lines_data:
            return JsonResponse({'error': 'Missing required fields.'}, status=400)

        supplier = Supplier.objects.get(id_supplier=supplier_id_str)
        default_status, _ = OrderStatus.objects.get_or_create(
            name='Draft', defaults={'symbol': 'DRF', 'description': 'Draft state'}
        )

        try:
            delivery_date = datetime.strptime(estimated_delivery_date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

        # Generar ID si es nueva orden
        if not edit_mode:
            max_id_result = PurchaseOrder.objects.aggregate(max_id=Max('id_purchase_order'))
            last_id_str = max_id_result.get('max_id')
            next_po_number = int(last_id_str) + 1 if last_id_str and last_id_str.isdigit() else 1
            next_po_id = str(next_po_number)
            purchase_order = PurchaseOrder.objects.create(
                id_purchase_order=next_po_id,
                id_supplier=supplier,
                estimated_delivery_date=delivery_date,
                order_status=default_status,
                created_by=request.user,
            )
        else:
            # Edición: actualizar orden existente
            purchase_order = get_object_or_404(PurchaseOrder, id_purchase_order=po_id)
            purchase_order.id_supplier = supplier
            purchase_order.estimated_delivery_date = delivery_date
            purchase_order.save()
            # Eliminar líneas anteriores y recrearlas (opcional: podría actualizar existentes)
            purchase_order.lines_purchase_order.all().delete()

        # Procesar líneas
        for i, line_data in enumerate(lines_data, start=1):
            material_id = line_data.get('id_material')
            unit_symbol = (line_data.get('unit_material') or line_data.get('unit', '')).strip().upper()
            currency_code = (line_data.get('currency_supplier', '')).strip().upper()
            quantity = line_data.get('quantity')
            price = line_data.get('price')
            position = line_data.get('position', i)

            if not all([material_id, unit_symbol, currency_code, quantity, price]):
                raise ValueError(f"Line {i}: missing fields.")

            material = Material.objects.get(id_material=material_id)
            unit_obj = Unit.objects.get(symbol=unit_symbol)
            currency_obj = Currency.objects.get(code=currency_code)

            quantity = float(quantity)
            price = float(price)

            line_po_id = f"{purchase_order.id_purchase_order}-{str(position).zfill(3)}"

            LinesPurchaseOrder.objects.create(
                id_purchase_order_line=line_po_id,
                id_purchase_order=purchase_order,
                id_material=material,
                position=position,
                quantity=quantity,
                unit_material=unit_obj,
                price=price,
                currency_supplier=currency_obj,
                receive_quantity=0,
                created_by=request.user,
            )

        response_data = {
            'success': True,
            'id_purchase_order': purchase_order.id_purchase_order,
            'message': f'Purchase Order {purchase_order.id_purchase_order} {"updated" if edit_mode else "created"} successfully',
            'redirect_url': '/purchases/purchase_order_list/'   # ← Corregido
        }
        return JsonResponse(response_data, status=201)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# ------------------------------------------------------------
# Eliminar orden de compra
# ------------------------------------------------------------
@login_required
def delete_purchase_order(request, pk):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__purchases')
    )['max_perm'] or 0
    if max_permission < 2:
        return redirect('purchases:purchase_order_list')

    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == 'POST':
        purchase_order.delete()
        return redirect('purchases:purchase_order_list')
    return redirect('purchases:purchase_order_list')