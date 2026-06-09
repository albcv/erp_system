from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Supplier, SupplierCategory, SupplierPaymentTerm, SupplierPaymentMethod, SupplierCurrency, SupplierCountry
from core.models import Status
from .forms import SupplierForm, CsvUploadForm
from django.core.paginator import Paginator
from django.db import models
from users.models import UserRole
from django.http import HttpResponse
from django.contrib import messages
import csv, io


# Create your views here.

@login_required
def supplier_list(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__suppliers')
    )['max_perm'] or 0
    if max_permission == 0:
        return redirect('dashboard')

    supplier_list = Supplier.objects.select_related('country', 'category', 'payment_terms', 'payment_method', 'currency', 'status').order_by('id_supplier')

    # Obtener parámetros de filtro
    id_supplier = request.GET.get('id_supplier', '').strip()
    name = request.GET.get('name', '').strip()
    country_id = request.GET.get('country')
    category_id = request.GET.get('category')
    status_id = request.GET.get('status')

    if id_supplier:
        supplier_list = supplier_list.filter(id_supplier__icontains=id_supplier)
    if name:
        supplier_list = supplier_list.filter(name__icontains=name)
    if country_id and country_id.isdigit():
        supplier_list = supplier_list.filter(country_id=int(country_id))
    if category_id and category_id.isdigit():
        supplier_list = supplier_list.filter(category_id=int(category_id))
    if status_id and status_id.isdigit():
        supplier_list = supplier_list.filter(status_id=int(status_id))

    if request.GET.get('export') == 'csv':
        return export_to_csv(supplier_list)

    paginator = Paginator(supplier_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'permissions': {'suppliers': max_permission},
        'countries': SupplierCountry.objects.all().order_by('name'),
        'categories': SupplierCategory.objects.all().order_by('name'),
        'statuses': Status.objects.all().order_by('name'),
    }
    return render(request, 'suppliers/supplier_list.html', context)


@login_required
def create_supplier(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__suppliers')
    )['max_perm'] or 0

    if max_permission == 0:
        return redirect('dashboard')
    if max_permission == 1:
        return redirect('suppliers:supplier_list')

    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.created_by = request.user
            supplier.save()

            # Determinar a dónde redirigir según el botón pulsado
            if 'create_continue' in request.POST:
                return redirect('suppliers:create_supplier')  
            else:
                return redirect('suppliers:supplier_list')
    else:
        form = SupplierForm()

    return render(request, 'suppliers/supplier_form.html', {'form': form})


@login_required
def edit_supplier(request, pk):

    supplier = get_object_or_404(Supplier,pk=pk)


    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__suppliers')
    )['max_perm'] or 0

    if max_permission == 0:
        return redirect('dashboard')
    if max_permission == 1:
        return redirect('suppliers:supplier_list')
    

    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)

        if form.is_valid():
            form.save()
            return redirect("suppliers:supplier_list")
        

    else:
        form = SupplierForm(instance=supplier)

    context = {
        'form':form,
        'supplier':supplier,
    }

    return render(request, 'suppliers/supplier_form.html', context)



@login_required
def delete_supplier(request, pk):

    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__suppliers')
    )['max_perm'] or 0

    if max_permission == 0:
        return redirect('dashboard')
    if max_permission == 1:
        return redirect('suppliers:supplier_list')


    supplier = get_object_or_404(Supplier, pk=pk)


    if request.method == 'POST':
        supplier.delete()
        
    return redirect('suppliers:supplier_list')
    

def export_to_csv(queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="suppliers.csv"'
    response.write('\ufeff'.encode('utf-8'))
    writer = csv.writer(response)
    writer.writerow([
        'ID Supplier', 'Legal Name', 'Name', 'Tax ID', 'Country', 'State/Province', 'City',
        'Address', 'Zip Code', 'Phone', 'Email', 'Contact Name', 'Contact Role',
        'Category', 'Payment Terms', 'Payment Method', 'Currency', 'Bank Account',
        'Status', 'Created By', 'Created At', 'Updated At'
    ])
    for s in queryset:
        writer.writerow([
            s.id_supplier, s.legal_name, s.name, s.tax_id,
            s.country.name if s.country else '',
            s.state_province, s.city, s.address, s.zip_code, s.phone, s.email,
            s.contact_name, s.contact_role,
            s.category.name if s.category else '',
            s.payment_terms.name if s.payment_terms else '',
            s.payment_method.name if s.payment_method else '',
            s.currency.code if s.currency else '',
            s.bank_account,
            s.status.name if s.status else '',
            s.created_by.username if s.created_by else 'N/A',
            s.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            s.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    return response

@login_required
def supplier_bulk_create(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__suppliers')
    )['max_perm'] or 0
    if max_permission == 0:
        return redirect('dashboard')
    if max_permission == 1:
        return redirect('suppliers:supplier_list')

    if request.method == 'POST':
        form = CsvUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            data_set = None
            try:
                data_set = csv_file.read().decode('UTF-8')
            except UnicodeDecodeError:
                try:
                    csv_file.seek(0)
                    data_set = csv_file.read().decode('ISO-8859-1')
                except Exception:
                    return render(request, 'suppliers/supplier_bulk_upload.html', {'form': form})
            if not data_set:
                return render(request, 'suppliers/supplier_bulk_upload.html', {'form': form})

            io_string = io.StringIO(data_set)
            reader = csv.DictReader(io_string)
            if reader.fieldnames:
                if reader.fieldnames[0].startswith('\ufeff'):
                    reader.fieldnames[0] = reader.fieldnames[0].lstrip('\ufeff')
                cleaned_fieldnames = [key.strip().lower() for key in reader.fieldnames]
                reader.fieldnames = cleaned_fieldnames

            # Mapas para FK
            country_map = {c.name.lower(): c for c in SupplierCountry.objects.all()}
            category_map = {cat.name.lower(): cat for cat in SupplierCategory.objects.all()}
            payment_terms_map = {pt.name.lower(): pt for pt in SupplierPaymentTerm.objects.all()}
            payment_method_map = {pm.name.lower(): pm for pm in SupplierPaymentMethod.objects.all()}
            currency_map = {curr.code.lower(): curr for curr in SupplierCurrency.objects.all()}
            status_map = {st.name.lower(): st for st in Status.objects.all()}

            successful_records = []
            error_records = []
            suppliers_to_create = []

            for i, row in enumerate(reader):
                row_number = i + 2
                form_data = {}
                for key, value in row.items():
                    cleaned_value = value.strip() if isinstance(value, str) else value
                    form_data[key] = cleaned_value

                # Mapear país por nombre
                country_name = form_data.get('country', '').strip().lower()
                country_obj = country_map.get(country_name)
                if not country_obj:
                    error_records.append({'row': row_number, 'data': row, 'errors': {'country': f'Country "{country_name}" not found'}})
                    continue
                form_data['country'] = country_obj.pk

                # Mapear categoría
                cat_name = form_data.get('category', '').strip().lower()
                category_obj = category_map.get(cat_name)
                if not category_obj:
                    error_records.append({'row': row_number, 'data': row, 'errors': {'category': f'Category "{cat_name}" not found'}})
                    continue
                form_data['category'] = category_obj.pk

                # Mapear payment_terms
                pt_name = form_data.get('payment_terms', '').strip().lower()
                pt_obj = payment_terms_map.get(pt_name)
                if not pt_obj:
                    error_records.append({'row': row_number, 'data': row, 'errors': {'payment_terms': f'Payment term "{pt_name}" not found'}})
                    continue
                form_data['payment_terms'] = pt_obj.pk

                # Mapear payment_method
                pm_name = form_data.get('payment_method', '').strip().lower()
                pm_obj = payment_method_map.get(pm_name)
                if not pm_obj:
                    error_records.append({'row': row_number, 'data': row, 'errors': {'payment_method': f'Payment method "{pm_name}" not found'}})
                    continue
                form_data['payment_method'] = pm_obj.pk

                # Mapear currency
                curr_code = form_data.get('currency', '').strip().lower()
                curr_obj = currency_map.get(curr_code)
                if not curr_obj:
                    error_records.append({'row': row_number, 'data': row, 'errors': {'currency': f'Currency "{curr_code}" not found'}})
                    continue
                form_data['currency'] = curr_obj.pk

                # Mapear status
                status_name = form_data.get('status', '').strip().lower()
                status_obj = status_map.get(status_name)
                if not status_obj:
                    error_records.append({'row': row_number, 'data': row, 'errors': {'status': f'Status "{status_name}" not found'}})
                    continue
                form_data['status'] = status_obj.pk

                # Crear formulario con los datos mapeados
                form = SupplierForm(form_data)
                if form.is_valid():
                    supplier = form.save(commit=False)
                    supplier.created_by = request.user
                    suppliers_to_create.append(supplier)
                    successful_records.append({'row': row_number, 'data': form_data})
                else:
                    errors = {field: ', '.join(err) for field, err in form.errors.items()}
                    error_records.append({'row': row_number, 'data': form_data, 'errors': errors})

            if suppliers_to_create:
                Supplier.objects.bulk_create(suppliers_to_create)

            messages.success(request, f'Process finished. {len(successful_records)} suppliers created.')
            context = {
                'form': CsvUploadForm(),
                'successful_count': len(successful_records),
                'error_count': len(error_records),
                'total_rows': len(successful_records) + len(error_records),
                'error_records': error_records,
                'successful_records': successful_records,
                'report_generated': True,
            }
            return render(request, 'suppliers/supplier_bulk_upload.html', context)
    else:
        form = CsvUploadForm()
    return render(request, 'suppliers/supplier_bulk_upload.html', {'form': form})

@login_required
def download_template_suppliers(request):
    header_fields = ['id_supplier', 'legal_name', 'name', 'tax_id', 'country', 'state_province', 'city', 'address',
                     'zip_code', 'phone', 'email', 'contact_name', 'contact_role', 'category', 'payment_terms',
                     'payment_method', 'currency', 'bank_account', 'status']
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="supplier_template.csv"'
    writer = csv.writer(response)
    writer.writerow(header_fields)
    return response