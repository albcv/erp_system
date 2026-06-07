from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Supplier
from .forms import SupplierForm
from django.core.paginator import Paginator
from django.db import models
from users.models import UserRole
from django.http import HttpResponse
import csv


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
        supplier_list = supplier_list.filter(status__icontains=status)

    
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
    
    
    