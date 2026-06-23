import logging, csv, json
from datetime import date, timedelta
from decimal import Decimal
from .models import Stock, InventoryMovement, Material
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from users.models import UserRole
from django.db import models, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.http import JsonResponse
from inventory.models import LocationInventory, MovementType
from django.core.paginator import Paginator
from core.models import Currency, ExchangeRate
from materials.models import Unit
from datetime import datetime




logger = logging.getLogger(__name__)

def sync_daily_stock():
    """
    Calcula el stock diario y el precio medio ponderado (PMP) en USD
    para cada material y ubicación, desde el primer movimiento hasta hoy.
    """
    try:
        # Obtener el primer movimiento para definir la fecha de inicio
        first_mov = InventoryMovement.objects.order_by('created_at').first()
        if not first_mov:
            logger.info("No inventory movements found. Nothing to sync.")
            return

        current_date = first_mov.created_at.date()
        today = date.today()

        # Diccionario para mantener balances acumulados por (material, ubicación)
        # Valor: (cantidad, pmp, unit_type_id)
        running_balances = {}

        # Precargar materiales para obtener unit_type
        material_cache = {m.id: m for m in Material.objects.select_related('unit').all()}

        while current_date <= today:
            # Movimientos del día actual
            daily_movs = InventoryMovement.objects.filter(
                created_at__date=current_date
            ).select_related('movement_type', 'id_material', 'id_location')

            materials_to_process = set(running_balances.keys())
            # Añadir los que tuvieron movimientos hoy
            for mov in daily_movs:
                materials_to_process.add((mov.id_material_id, mov.id_location_id))

            for mat_id, loc_id in materials_to_process:
                key = (mat_id, loc_id)
                # Recuperar balance anterior o inicializar
                prev_qty, prev_pmp, unit_type_id = running_balances.get(key, (Decimal(0), Decimal('0.0'), None))

                # Obtener la unidad del material 
                if unit_type_id is None:
                    material = material_cache.get(mat_id)
                    if material and material.unit:
                        unit_type_id = material.unit.id
                    else:
                    
                        movs_for_mat = [m for m in daily_movs if m.id_material_id == mat_id]
                        if movs_for_mat:
                            unit_type_id = movs_for_mat[0].unit_type_id
                        else:
                            # Si no hay movimientos y no tenemos unidad, saltamos (no debería ocurrir)
                            logger.warning(f"No unit found for material {mat_id}. Skipping stock update.")
                            continue

                # Movimientos de este día para este material y ubicación
                mat_movs = [m for m in daily_movs if m.id_material_id == mat_id and m.id_location_id == loc_id]

                # Inicializar valores del día
                current_qty = prev_qty
                total_cost_usd = prev_qty * prev_pmp

                for mov in mat_movs:
                    # Obtener precio en USD
                    exchange_rate = Decimal(mov.exchange_rate) if mov.exchange_rate else Decimal('1.0')
                    if exchange_rate == 0:
                        exchange_rate = Decimal('1.0')
                        logger.warning(f"Exchange rate is zero for movement {mov.id}. Using 1.0.")

                    price_usd = Decimal(mov.price) / exchange_rate
                    quantity = Decimal(mov.quantity)

                    if mov.movement_type.symbol == 'PUR':  # Compra
                        total_cost_usd += quantity * price_usd
                        current_qty += quantity
                    elif mov.movement_type.symbol in ['SAL', 'OUT', 'RET']:  # Salidas
                        if current_qty >= quantity:
                            current_qty -= quantity
                        else:
                            logger.warning(f"Negative stock for material {mat_id} at location {loc_id} on {current_date}")
                            current_qty = 0
                  

                # Calcular PMP si hay stock
                if current_qty > 0:
                    current_pmp = total_cost_usd / current_qty
                else:
                    current_pmp = Decimal('0.0')
                    total_cost_usd = Decimal('0.0')

                # Guardar o actualizar el registro de stock diario
                Stock.objects.update_or_create(
                    date=current_date,
                    id_location_id=loc_id,
                    id_material_id=mat_id,
                    defaults={
                        'quantity': current_qty,
                        'avg_price_usd': current_pmp,
                        'unit_type_id': unit_type_id,  
                    }
                )

                # Actualizar balance acumulado para el día siguiente
                running_balances[key] = (current_qty, current_pmp, unit_type_id)

            # Avanzar al siguiente día
            current_date += timedelta(days=1)

        logger.info(f"Stock sync completed successfully up to {today}.")

    except Exception as e:
        logger.error(f"Error syncing daily stock: {e}", exc_info=True)
        raise


@login_required
def movement_list(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__inventory')
    )['max_perm'] or 0
    if max_permission == 0:
        return redirect('dashboard')

    movements = InventoryMovement.objects.select_related(
        'id_location', 'id_material', 'unit_type', 'movement_type', 'currency', 'created_by'
    ).order_by('-created_at')

   
    if request.GET.get('location'):
        movements = movements.filter(id_location_id=request.GET.get('location'))
    if request.GET.get('type'):
        movements = movements.filter(movement_type_id=request.GET.get('type'))

   
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        movements = movements.filter(created_at__date__gte=date_from)
    if date_to:
        movements = movements.filter(created_at__date__lte=date_to)

    # Exportación CSV
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventory_movements.csv"'
        response.write('\ufeff'.encode('utf-8'))
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Date', 'Location', 'Material', 'Unit', 'Quantity',
            'Movement Type', 'Price', 'Currency', 'User'
        ])
        for m in movements:
            writer.writerow([
                m.id_inventory_movement,
                m.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                m.id_location.name,
                m.id_material.name,
                m.unit_type.symbol,
                m.quantity,
                m.movement_type.name,
                m.price,
                m.currency.symbol,
                m.created_by.username if m.created_by else 'N/A'
            ])
        return response

    # Paginación
    paginator = Paginator(movements, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'locations': LocationInventory.objects.all().order_by('name'),
        'mov_types': MovementType.objects.all().order_by('name'),
       
    }
    return render(request, 'inventory/movement_list.html', context)



@login_required
def stock_list(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__inventory')
    )['max_perm'] or 0
    if max_permission == 0:
        return redirect('dashboard')
    
    date_filter = request.GET.get('date')
    if not date_filter:
       
        date_filter = date.today().isoformat()
    
    # Query con select_related
    stocks = Stock.objects.select_related('id_location', 'id_material', 'unit_type').order_by('-date', 'id_location', 'id_material')
    
    if date_filter:
        stocks = stocks.filter(date=date_filter)
    if request.GET.get('location'):
        stocks = stocks.filter(id_location_id=request.GET.get('location'))

    # Exportación CSV
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="stock_report.csv"'
        response.write('\ufeff'.encode('utf-8'))
        writer = csv.writer(response)
        writer.writerow([
            'Date', 'Location', 'Material', 'Quantity', 'Unit', 
            'AVG Price (USD)', 'Total Value (USD)'
        ])
        for s in stocks:
            writer.writerow([
                s.date,
                s.id_location.name,
                s.id_material.name,
                s.quantity,
                s.unit_type.symbol,  
                s.avg_price_usd,
                s.total_value_usd,
            ])
        return response

    # Paginación
    paginator = Paginator(stocks, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'locations': LocationInventory.objects.all().order_by('name'),
        'current_date': date_filter, 
    }
    return render(request, 'inventory/stock_list.html', context)


@login_required
def create_movement(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__inventory')
    )['max_perm'] or 0
    if max_permission == 0:
        return redirect('dashboard')
    if max_permission == 1:
        return redirect('inventory:movement_list')

    context = {
        'title': 'Create Inventory Movement',
        'locations': LocationInventory.objects.filter(status__is_active=True).order_by('name'),
        'movement_types': MovementType.objects.all().order_by('name'),
        'materials': Material.objects.filter(status__name='Active').order_by('name'),
        'currencies': Currency.objects.all().order_by('code'),
        'units': Unit.objects.all().order_by('symbol'),
    }
    return render(request, 'inventory/movement_form.html', context)



@csrf_exempt
@require_POST
@transaction.atomic
@login_required
def post_inventory_movement(request):
    try:
        data = json.loads(request.body)

        location_id = data.get('location')
        material_id = data.get('material')
        quantity = data.get('quantity')
        unit_id = data.get('unit')
        movement_type_id = data.get('movement_type')
        price = data.get('price')
        currency_id = data.get('currency')

        # Validaciones básicas
        if not all([location_id, material_id, quantity, unit_id, movement_type_id, price, currency_id]):
            return JsonResponse({'error': 'All fields are required.'}, status=400)

        quantity = int(quantity)
        if quantity <= 0:
            return JsonResponse({'error': 'Quantity must be greater than zero.'}, status=400)

        price = float(price)
        if price < 0:
            return JsonResponse({'error': 'Price cannot be negative.'}, status=400)

        # Obtener objetos relacionados
        location = get_object_or_404(LocationInventory, pk=location_id)
        material = get_object_or_404(Material, pk=material_id)
        unit = get_object_or_404(Unit, pk=unit_id)
        movement_type = get_object_or_404(MovementType, pk=movement_type_id)
        currency = get_object_or_404(Currency, pk=currency_id)

        # Obtener tipo de cambio para la moneda (fecha actual)
        today = datetime.now().date()
        exchange_rate_obj = ExchangeRate.objects.filter(
            currency=currency,
            date__lte=today
        ).order_by('-date').first()

        exchange_rate = exchange_rate_obj.rate if exchange_rate_obj else 1.0

        # Generar ID de movimiento (secuencial)
        last_mov = InventoryMovement.objects.order_by('-id').first()
        next_id = (last_mov.id + 1) if last_mov else 1
        movement_id = f"MOV-{str(next_id).zfill(6)}"

        # Crear el movimiento
        movement = InventoryMovement.objects.create(
            id_inventory_movement=movement_id,
            id_location=location,
            id_material=material,
            quantity=quantity,
            unit_type=unit,
            movement_type=movement_type,
            price=price,
            currency=currency,
            exchange_rate=exchange_rate,
            created_by=request.user,
        )

        return JsonResponse({
            'success': True,
            'message': f'Movement {movement.id_inventory_movement} created successfully.',
            'redirect_url': '/inventory/movement_list/'
        }, status=201)

    except ValueError as e:
        return JsonResponse({'error': f'Validation error: {str(e)}'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)
    

@login_required
def edit_movement(request, pk):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__inventory')
    )['max_perm'] or 0
    if max_permission == 0:
        return redirect('dashboard')
    if max_permission == 1:
        return redirect('inventory:movement_list')

    movement = get_object_or_404(InventoryMovement, pk=pk)

    context = {
        'title': 'Edit Inventory Movement',
        'movement': movement,
        'locations': LocationInventory.objects.filter(status__is_active=True).order_by('name'),
        'movement_types': MovementType.objects.all().order_by('name'),
        'materials': Material.objects.filter(status__name='Active').order_by('name'),
        'currencies': Currency.objects.all().order_by('code'),
        'units': Unit.objects.all().order_by('symbol'),
        'is_edit': True,
    }
    return render(request, 'inventory/movement_form.html', context)


@csrf_exempt
@require_POST
@transaction.atomic
@login_required
def update_inventory_movement(request, pk):
    try:
        data = json.loads(request.body)
        movement = get_object_or_404(InventoryMovement, pk=pk)

        # Actualizar campos
        movement.id_location_id = data.get('location')
        movement.id_material_id = data.get('material')
        movement.quantity = int(data.get('quantity'))
        movement.unit_type_id = data.get('unit')
        movement.movement_type_id = data.get('movement_type')
        movement.price = float(data.get('price'))
        movement.currency_id = data.get('currency')

    

        movement.save()

        return JsonResponse({
            'success': True,
            'message': f'Movement {movement.id_inventory_movement} updated successfully.',
            'redirect_url': '/inventory/movement_list/'
        }, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    


@login_required
def delete_movement(request, pk):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__inventory')
    )['max_perm'] or 0
    if max_permission < 2:
        return redirect('inventory:movement_list')

    movement = get_object_or_404(InventoryMovement, pk=pk)
    if request.method == 'POST':
        movement.delete()
        return redirect('inventory:movement_list')
    return redirect('inventory:movement_list')