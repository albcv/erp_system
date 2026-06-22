import json
from django.core.serializers.json import DjangoJSONEncoder
import csv
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Max, F, Sum
from django.db import transaction, models
from django.core.paginator import Paginator
from django.db.models import Q
from .models import PurchaseOrder, LinesPurchaseOrder, OrderStatus, PurchaseInvoice, InvoiceStatus, LinesPurchaseInvoice
from suppliers.models import Supplier
from materials.models import Material, Unit
from core.models import Currency
from users.models import UserRole
from inventory.models import LocationInventory, InventoryMovement, MovementType
from .models import GoodsReceipt, LinesGoodsReceipt, GoodsReceiptStatus
from accounting.models import AccountAccount, Journal


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

    purchase_orders = PurchaseOrder.objects.select_related('id_supplier', 'order_status', 'created_by').all().order_by('id_purchase_order', '-issue_date')

    id_po = request.GET.get('id_purchase_order')
    supplier_input = request.GET.get('supplier_id')
    status_symbol = request.GET.get('status_symbol')

    if id_po:
        purchase_orders = purchase_orders.filter(id_purchase_order__icontains=id_po)
    if supplier_input:
        purchase_orders = purchase_orders.filter(
            Q(id_supplier__id_supplier__icontains=supplier_input) |
            Q(id_supplier__name__icontains=supplier_input)
        )
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
        lines = purchase_order.lines_purchase_order.all().order_by('position')
        if max_permission < 2:
            return redirect('purchases:purchase_order_list')

        # Preparar datos serializables para JSON
        po_data = {
            'id_purchase_order': purchase_order.id_purchase_order,
            'estimated_delivery_date': purchase_order.estimated_delivery_date.strftime('%Y-%m-%d') if purchase_order.estimated_delivery_date else None,
            'order_status_id': purchase_order.order_status.pk,
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

    currencies_qs = Currency.objects.all().order_by('code')
    currencies_list = [{'code': c.code, 'name': c.name} for c in currencies_qs]

    context = {
        'title': 'Edit Purchase Order' if purchase_order else 'Create New Purchase Order',
        'purchase_order': purchase_order,
        'lines': lines,
        'purchase_order_json': purchase_order_json,
        'lines_json': lines_json,
        'currencies': currencies_list,
        'statuses': OrderStatus.objects.all().order_by('name'),
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
        po_id = data.get('id_purchase_order')
        order_status_id = data.get('order_status')

        if not supplier_id_str or not estimated_delivery_date_str or not lines_data:
            return JsonResponse({'error': 'Missing required fields.'}, status=400)

        supplier = Supplier.objects.get(id_supplier=supplier_id_str)

        if order_status_id:
            try:
                order_status = OrderStatus.objects.get(pk=order_status_id)
            except OrderStatus.DoesNotExist:
                return JsonResponse({'error': 'Invalid order status'}, status=400)
        else:
            order_status, _ = OrderStatus.objects.get_or_create(
                name='Draft', defaults={'symbol': 'DRF', 'description': 'Draft state'}
            )

        try:
            delivery_date = datetime.strptime(estimated_delivery_date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

        if not edit_mode:
            max_id_result = PurchaseOrder.objects.aggregate(max_id=Max('id_purchase_order'))
            last_id_str = max_id_result.get('max_id')
            next_po_number = int(last_id_str) + 1 if last_id_str and last_id_str.isdigit() else 1
            next_po_id = str(next_po_number)
            purchase_order = PurchaseOrder.objects.create(
                id_purchase_order=next_po_id,
                id_supplier=supplier,
                estimated_delivery_date=delivery_date,
                order_status=order_status,
                created_by=request.user,
            )
        else:
            purchase_order = get_object_or_404(PurchaseOrder, id_purchase_order=po_id)
            purchase_order.id_supplier = supplier
            purchase_order.estimated_delivery_date = delivery_date
            purchase_order.order_status = order_status
            purchase_order.save()
            purchase_order.lines_purchase_order.all().delete()

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
            'redirect_url': '/purchases/purchase_order_list/'
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

# ------------------------------------------------------------
# Formulario de recepción de mercancías
# ------------------------------------------------------------
@login_required
def goods_receipt_form(request, po_pk=None):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__purchases')
    )['max_perm'] or 0
    if max_permission == 0:
        return redirect('dashboard')
    if max_permission == 1:
        return redirect('purchases:purchase_order_list')

    purchase_order = get_object_or_404(PurchaseOrder, pk=po_pk)

    # Filtrar líneas con cantidad pendiente por recibir
    order_lines = LinesPurchaseOrder.objects.filter(
        id_purchase_order=purchase_order
    ).exclude(quantity__lte=F('receive_quantity')).order_by('position')

    if not order_lines.exists():
        return redirect('purchases:purchase_order_list')

    for line in order_lines:
        line.pending_quantity = line.quantity - line.receive_quantity

    locations = LocationInventory.objects.filter(status__is_active=True).order_by('code')

    context = {
        'purchase_order': purchase_order,
        'order_lines': order_lines,
        'locations': locations,
    }
    return render(request, 'purchases/goods_receipt_form.html', context)

# ------------------------------------------------------------
# Procesar recepción de mercancías (vía AJAX POST)
# ------------------------------------------------------------
@csrf_exempt
@require_POST
@transaction.atomic
@login_required
def post_goods_receipt(request):
    try:
        data = json.loads(request.body)

        po_pk = data.get('po_pk')
        receipt_date = data.get('receipt_date')
        lines_data = data.get('lines', [])

        if not lines_data:
            return JsonResponse({'error': 'Must receive at least 1 quantity.'}, status=400)

        purchase_order = get_object_or_404(PurchaseOrder, pk=po_pk)

        # Asegurar que existe un MovementType con símbolo 'PUR' (o el que uses)
        movement_type_pur, _ = MovementType.objects.get_or_create(
            symbol='PUR',
            defaults={'name': 'Purchase Receipt', 'created_by': request.user}
        )

        # Generar ID de recepción usando el autoincrement id (más seguro)
        last_gr = GoodsReceipt.objects.order_by('-id').first()
        next_gr_number = (last_gr.id + 1) if last_gr else 1
        next_gr_id = str(next_gr_number).zfill(10)

        # Obtener estado "COMPLETED" (crearlo si no existe)
        gr_status_completed, _ = GoodsReceiptStatus.objects.get_or_create(
            symbol="COMPLETED",
            defaults={'name': 'Completed', 'created_by': request.user}
        )

        # Crear GoodsReceipt
        goods_receipt = GoodsReceipt.objects.create(
            id_goods_receipt=next_gr_id,
            id_purchase_order=purchase_order,
            receipt_date=receipt_date,
            status=gr_status_completed,
            created_by=request.user,
        )

        total_ordered_qty = purchase_order.lines_purchase_order.aggregate(total=Sum('quantity'))['total'] or 0
        total_previously_received = purchase_order.lines_purchase_order.aggregate(total=Sum('receive_quantity'))['total'] or 0
        total_received_in_this_gr = 0

        for i, line_data in enumerate(lines_data, start=1):
            line_pk = line_data['line_pk']
            received_qty = int(line_data['received_quantity'])
            location_pk = line_data['location_pk']

            po_line = get_object_or_404(LinesPurchaseOrder, pk=line_pk)
            location = get_object_or_404(LocationInventory, pk=location_pk)

            if received_qty <= 0:
                continue

            available_to_receive = po_line.quantity - po_line.receive_quantity
            if received_qty > available_to_receive:
                raise ValueError(f"Over reception in line {po_line.position}. Ordered: {po_line.quantity}, Already received: {po_line.receive_quantity}, Trying to receive: {received_qty}")

            # Crear movimiento de inventario
            inventory_movement = InventoryMovement.objects.create(
                id_inventory_movement=f"GR-{next_gr_id}-{i}",
                id_location=location,
                id_material=po_line.id_material,
                quantity=received_qty,
                unit_type=po_line.unit_material,
                movement_type=movement_type_pur,
                price=po_line.price,
                currency=po_line.currency_supplier,
                created_by=request.user,
            )

            line_gr_id = f"{next_gr_id}-{str(i).zfill(3)}"
            LinesGoodsReceipt.objects.create(
                id_goods_receipt_line=line_gr_id,
                id_goods_receipt=goods_receipt,
                id_purchase_order_line=po_line,
                id_material=po_line.id_material,
                receive_quantity=received_qty,                
                unit_material=po_line.unit_material,
                id_location=location,
                inventory_movement_ref=inventory_movement.id_inventory_movement,  
                created_by=request.user,
            )

            po_line.receive_quantity += received_qty
            po_line.save()

            total_received_in_this_gr += received_qty

        total_final_received = total_previously_received + total_received_in_this_gr

        # Actualizar estado de la orden de compra
        status_completed, _ = OrderStatus.objects.get_or_create(
            symbol="RECEIVED",
            defaults={'name': 'Received', 'created_by': request.user}
        )
        status_partially_received, _ = OrderStatus.objects.get_or_create(
            symbol="PARTIAL_RECEIVED",
            defaults={'name': 'Partially Received', 'created_by': request.user}
        )

        if total_final_received >= total_ordered_qty:
            purchase_order.order_status = status_completed
        elif total_final_received > 0:
            purchase_order.order_status = status_partially_received
        purchase_order.save()

        response_data = {
            'success': True,
            'id_goods_receipt': next_gr_id,
            'redirect_url': f'/purchases/edit/{po_pk}/',
        }
        return JsonResponse(response_data, status=200)

    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format in request body.'}, status=400)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return JsonResponse({'error': f'An unexpected server error occurred: {str(e)}'}, status=500)

# ------------------------------------------------------------
# Formulario de facturación de compras
# ------------------------------------------------------------
@login_required
def purchase_invoice_form(request, po_pk=None):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__purchases')
    )['max_perm'] or 0
    if max_permission == 0:
        return redirect('dashboard')
    if max_permission == 1:
        return redirect('purchases:purchase_order_list')

    purchase_order = get_object_or_404(PurchaseOrder, pk=po_pk)

    # Verificar que la orden no esté ya facturada o cerrada
    if purchase_order.order_status.symbol in ['CLOSED', 'INVOICED']:
        messages.warning(request, f"The purchase order {po_pk} is already invoiced or closed. It's not possible to create a new invoice")
        return redirect('purchases:edit_purchase_order', pk=po_pk)

    order_lines = LinesPurchaseOrder.objects.filter(id_purchase_order=purchase_order).order_by('position')
    currency = purchase_order.id_supplier.currency

    total_amount = sum(line.quantity * line.price for line in order_lines)

    context = {
        'purchase_order': purchase_order,
        'order_lines': order_lines,
        'currency': currency,
        'total_ordered_amount': total_amount,
    }
    return render(request, 'purchases/purchase_invoice_form.html', context)

# ------------------------------------------------------------
# Procesar factura de compra (vía AJAX POST)
# ------------------------------------------------------------
@csrf_exempt
@require_POST
@transaction.atomic
@login_required
def post_purchase_invoice(request):
    try:
        data = json.loads(request.body)

        po_pk = data.get('po_pk')
        due_date = data.get('due_date')
        lines_data = data.get('lines', [])

        if not lines_data or not due_date:
            return JsonResponse({'error': 'Missing lines or due date'}, status=400)

        purchase_order = get_object_or_404(PurchaseOrder, pk=po_pk)

        if purchase_order.order_status.symbol in ['CLOSED', 'INVOICED']:
            return JsonResponse({'error': f'Purchase order {po_pk} is already invoiced or closed.'}, status=400)

        # Generar ID de factura
        max_id_result = PurchaseInvoice.objects.aggregate(max_id=Max('id_invoice'))
        last_id_str = max_id_result.get('max_id')
        if last_id_str and last_id_str.isdigit():
            next_invoice_number = int(last_id_str) + 1
        else:
            next_invoice_number = 1
        next_invoice_id = str(next_invoice_number).zfill(10)

        # Estado de la factura (asumimos que existe "PENDING")
        invoice_status_pending, _ = InvoiceStatus.objects.get_or_create(
            symbol="PENDING",
            defaults={'name': 'Pending', 'created_by': request.user}
        )

        total_amount = 0
        invoiced_lines = []

        # Procesar líneas
        for i, line_data in enumerate(lines_data, start=1):
            po_line = get_object_or_404(LinesPurchaseOrder, pk=line_data['line_pk'])
            qty_to_invoice = int(line_data['quantity_to_invoice'])

            if qty_to_invoice <= 0:
                continue

            line_total = qty_to_invoice * po_line.price
            total_amount += line_total

            line_invoice_id = f"{next_invoice_id}-{str(i).zfill(3)}"
            invoice_line = LinesPurchaseInvoice(
                id_invoice_line=line_invoice_id,
                id_purchase_order_line=po_line,
                price=po_line.price,
                quantity=qty_to_invoice,
                currency_invoice_line=po_line.currency_supplier,   # ← CORREGIDO
                created_by=request.user,
            )
            invoiced_lines.append(invoice_line)

        if total_amount == 0:
            return JsonResponse({'error': 'Total amount is zero. Check quantities.'}, status=400)

        # Crear la factura
        purchase_invoice = PurchaseInvoice.objects.create(
            id_invoice=next_invoice_id,
            id_purchase_order=purchase_order,
            due_date=due_date,
            total_amount=total_amount,
            currency_invoice=purchase_order.id_supplier.currency,
            status=invoice_status_pending,   # ← usar InvoiceStatus
            created_by=request.user,
        )

        # Guardar líneas de la factura
        for line in invoiced_lines:
            line.id_purchase_invoice = purchase_invoice
            line.save()

        # Asientos contables (usar get_or_create para evitar errores si no existen)
        purchase_account, _ = AccountAccount.objects.get_or_create(
            code='1200',
            defaults={
                'name': 'Inventory Purchases',
                'account_type_id': 1,
                'account_group_id': 1,
                'nature_id': 1,
                'currency_id': purchase_order.id_supplier.currency.pk,
                'country_id': 1,
                'status_id': 1,
                'created_by': request.user
            }
        )
        bank_account, _ = AccountAccount.objects.get_or_create(
            code='1001',
            defaults={
                'name': 'Bank Account',
                'account_type_id': 1,
                'account_group_id': 1,
                'nature_id': 1,
                'currency_id': purchase_order.id_supplier.currency.pk,
                'country_id': 1,
                'status_id': 1,
                'created_by': request.user
            }
        )

        group_id = purchase_invoice.id_invoice

        # Asiento de débito (compra)
        Journal.objects.create(
            id_journal=f"INV-{group_id}-D1",
            group_journal=group_id,
            reference=f"INV-{group_id} - Inventory/Purchases (Paid)",
            id_account=purchase_account,
            credit=0.0,
            debit=total_amount,
            currency=purchase_order.id_supplier.currency,
            created_by=request.user
        )

        # Asiento de crédito (pago desde banco)
        Journal.objects.create(
            id_journal=f"INV-{group_id}-C1",
            group_journal=group_id,
            reference=f"INV-{group_id} - Payment from bank",
            id_account=bank_account,
            credit=total_amount,
            debit=0.0,
            currency=purchase_order.id_supplier.currency,
            created_by=request.user
        )

        # Actualizar estado de la orden de compra
        status_received, _ = OrderStatus.objects.get_or_create(
            symbol="RECEIVED",
            defaults={'name': 'Received', 'created_by': request.user}
        )
        status_closed, _ = OrderStatus.objects.get_or_create(
            symbol="CLOSED",
            defaults={'name': 'Closed', 'created_by': request.user}
        )
        status_invoiced, _ = OrderStatus.objects.get_or_create(
            symbol="INVOICED",
            defaults={'name': 'Invoiced', 'created_by': request.user}
        )

        if purchase_order.order_status.symbol == status_received.symbol:
            purchase_order.order_status = status_closed
        else:
            purchase_order.order_status = status_invoiced
        purchase_order.save()

        response_data = {
            'success': True,
            'id_invoice': next_invoice_id,
            'redirect_url': f'/purchases/edit/{po_pk}/',
        }
        return JsonResponse(response_data, status=200)

    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format in request body.'}, status=400)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return JsonResponse({'error': f'An unexpected server error occurred: {str(e)}'}, status=500)


@login_required
def mark_invoice_paid(request, invoice_id):
    invoice = get_object_or_404(PurchaseInvoice, id_invoice=invoice_id)
    # Cambiar estado a PAID
    paid_status, _ = InvoiceStatus.objects.get_or_create(symbol="PAID", defaults={'name': 'Paid'})
    invoice.status = paid_status
    invoice.save()
    return JsonResponse({'success': True, 'redirect_url': f'/purchases/edit/{invoice.id_purchase_order.pk}/'})