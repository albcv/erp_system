from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Supplier
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
    

    supplier_list = Supplier.objects.all().order_by('id_supplier')

    id_supplier = request.GET.get('id_supplier')
    name = request.GET.get('name')
    country = request.GET.get('country')
    status = request.GET.get('status')

    if id_supplier:
        supplier_list = supplier_list.filter(id_supplier__icontains=id_supplier)

    if name:
        supplier_list = supplier_list.filter(name__icontains=name)

    if country:
        supplier_list = supplier_list.filter(country__icontains=country)

    if status is not None and status != '':
        supplier_list = supplier_list.filter(status=status)

    
    if request.GET.get('export') == 'csv':
        return export_to_csv(supplier_list)

    paginator = Paginator(supplier_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'suppliers/supplier_list.html', {'page_obj': page_obj})


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
    """Exporta el queryset de suppliers a un archivo CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="suppliers.csv"'
    response.write('\ufeff'.encode("utf-8"))
    writer = csv.writer(response)

   
    writer.writerow([
        'ID Supplier', 'Legal Name', 'Name', 'Tax ID', 'Country', 'State/Province', 'City',
        'Address', 'Zip Code', 'Phone', 'Email', 'Contact Name', 'Contact Role',
        'Category', 'Payment Terms', 'Payment Method', 'Currency', 'Bank Account',
        'Status', 'Created By', 'Created At', 'Updated At'
    ])

    for supplier in queryset:
        writer.writerow([
            supplier.id_supplier,
            supplier.legal_name,
            supplier.name,
            supplier.tax_id,
            supplier.country,
            supplier.state_province,
            supplier.city,
            supplier.address,
            supplier.zip_code,
            supplier.phone,
            supplier.email,
            supplier.contact_name,
            supplier.contact_role,
            supplier.category,
            supplier.payment_terms,
            supplier.payment_method,
            supplier.currency,
            supplier.bank_account,
            supplier.status,
            supplier.created_by.username if supplier.created_by else 'N/A',
            supplier.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            supplier.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
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

            successful_records = [] 
            error_records = []
            suppliers_to_create = []  

            for i, row in enumerate(reader):
                row_number = i + 2
                form_data = {}

                for key, value in row.items():
                    cleaned_value = value.strip() if isinstance(value, str) else value
                    form_data[key] = cleaned_value

                form = SupplierForm(form_data)

                if form.is_valid():
                    supplier = form.save(commit=False)
                    supplier.created_by = request.user
                    suppliers_to_create.append(supplier)
                    successful_records.append({'row': row_number, 'data': form_data})
                else:
                    errors = {field: ', '.join(err) for field, err in form.errors.items()}
                    error_records.append({
                        'row': row_number,
                        'data': form_data,
                        'errors': errors
                    })

            # Crear los proveedores en lote
            if suppliers_to_create:
                Supplier.objects.bulk_create(suppliers_to_create)

            messages.success(request, f'Process finished. {len(successful_records)} suppliers created successfully.')

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
    header_fields = ['id_supplier', 'legal_name', 'name', 'tax_id', 'country', 'state_province', 'city', 'address', 'zip_code', 'phone', 'email', 'contact_name',
                           'contact_role', 'category', 'payment_terms','payment_method', 'currency', 'bank_account', 'status']
    
    response = HttpResponse(content_type = 'text/csv')
    response['Content-Disposition'] = 'attachment;filename="supplier_template.csv"'

    writer = csv.writer(response)
    writer.writerow(header_fields)

    return response