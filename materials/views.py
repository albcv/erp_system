from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Material
from .forms import MaterialForm, CsvUploadForm
from django.core.paginator import Paginator
from django.db import models
from users.models import UserRole
from django.http import HttpResponse
import csv, io


# Create your views here.

@login_required
def material_list(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__materials')
    )['max_perm'] or 0

    if max_permission == 0:
        return redirect('dashboard')
    

    material_list = Material.objects.all().order_by('id_material')

    id_material = request.GET.get('id_material')
    name = request.GET.get('name')
    material_type = request.GET.get('material_type')
    status = request.GET.get('status')

    if id_material:
        material_list = material_list.filter(id_material__icontains=id_material)

    if name:
        material_list = material_list.filter(name__icontains=name)

    if material_type:
        material_list = material_list.filter(material_type__icontains=material_type)

    if status is not None and status != '':
        material_list = material_list.filter(status=status)

    
    if request.GET.get('export') == 'csv':
        return export_to_csv(material_list)

    paginator = Paginator(material_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'materials/material_list.html', {'page_obj': page_obj})


@login_required
def create_material(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__materials')
    )['max_perm'] or 0

    if max_permission == 0:
        return redirect('dashboard')
    if max_permission == 1:
        return redirect('materials:material_list')

    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            material = form.save(commit=False)
            material.created_by = request.user
            material.save()

            # Determinar a dónde redirigir según el botón pulsado
            if 'create_continue' in request.POST:
                return redirect('materials:create_material')  
            else:
                return redirect('materials:material_list')
    else:
        form = MaterialForm()

    return render(request, 'materials/material_form.html', {'form': form})


@login_required
def edit_material(request, pk):

    material = get_object_or_404(Material,pk=pk)


    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__materials')
    )['max_perm'] or 0

    if max_permission == 0:
        return redirect('dashboard')
    if max_permission == 1:
        return redirect('materials:material_list')
    

    if request.method == 'POST':
        form = MaterialForm(request.POST, instance=material)

        if form.is_valid():
            form.save()
            return redirect("materials:material_list")
        

    else:
        form = MaterialForm(instance=material)

    context = {
        'form':form,
        'material':material,
    }

    return render(request, 'materials/material_form.html', context)



@login_required
def delete_material(request, pk):

    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__materials')
    )['max_perm'] or 0

    if max_permission == 0:
        return redirect('dashboard')
    if max_permission == 1:
        return redirect('materials:material_list')


    material = get_object_or_404(Material, pk=pk)


    if request.method == 'POST':
        material.delete()
        
    return redirect('materials:material_list')
    


def export_to_csv(queryset):
    """Exporta el queryset de materiales a un archivo CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="materials.csv"'
    response.write('\ufeff'.encode("utf-8")) 
    writer = csv.writer(response)

    writer.writerow(['ID Material', 'Name', 'Description', 'Unit', 'Type', 'Status', 'Created_by', 'Created_at', 'Updated_at'])

    for material in queryset:
        writer.writerow([
            material.id_material,
            material.name,
            material.description,
            material.unit,
            material.material_type,
            material.status,
            material.created_by.username if material.created_by else 'N/A',
            material.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            material.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])

    return response



@login_required
def material_bulk_create(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_perm=models.Max('role__materials')
    )['max_perm'] or 0

    if max_permission == 0:
        return redirect('dashboard')
    if max_permission == 1:
        return redirect('materials:material_list')

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
                    return render(request, 'materials/material_bulk_upload.html', {'form': form})

            if not data_set:
                return render(request, 'materials/material_bulk_upload.html', {'form': form})

            io_string = io.StringIO(data_set)
            reader = csv.DictReader(io_string)

            if reader.fieldnames:
                if reader.fieldnames[0].startswith('\ufeff'):
                    reader.fieldnames[0] = reader.fieldnames[0].lstrip('\ufeff')
                cleaned_fieldnames = [key.strip().lower() for key in reader.fieldnames]
                reader.fieldnames = cleaned_fieldnames

            successful_records = []
            error_records = []
            materials_to_create = []

            for i, row in enumerate(reader):
                row_number = i + 2
                form_data = {}
                for key, value in row.items():
                    cleaned_value = value.strip() if isinstance(value, str) else value
                    form_data[key] = cleaned_value

                form = MaterialForm(form_data)

                if form.is_valid():
                    material = form.save(commit=False)
                    material.created_by = request.user
                    materials_to_create.append(material)
                    successful_records.append({'row': row_number, 'data': form_data})
                else:
                    errors = {field: ', '.join(err) for field, err in form.errors.items()}
                    error_records.append({
                        'row': row_number,
                        'data': form_data,
                        'errors': errors
                    })

            if materials_to_create:
                Material.objects.bulk_create(materials_to_create)

            messages.success(request, f'Process finished. {len(successful_records)} materials created successfully.')

            context = {
                'form': CsvUploadForm(),
                'successful_count': len(successful_records),
                'error_count': len(error_records),
                'total_rows': len(successful_records) + len(error_records),
                'error_records': error_records,
                'successful_records': successful_records,
                'report_generated': True,
            }
            return render(request, 'materials/material_bulk_upload.html', context)

    else:
        form = CsvUploadForm()

    return render(request, 'materials/material_bulk_upload.html', {'form': form})


@login_required
def download_template_materials(request):
    header_fields = [
        'id_material', 'name', 'description', 'unit', 'material_type', 'status'
    ]
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="material_template.csv"'
    writer = csv.writer(response)
    writer.writerow(header_fields)
    return response

    
    
    