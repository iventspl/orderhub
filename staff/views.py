from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from users.models import UserProfile, User
from django.views.decorators.http import require_POST
from .forms import StaffAddForm
from django.http import JsonResponse

# Create your views here.
@login_required
def staff_dashboard(request):
    is_admin = request.user.profile.assigned_role == 'ADMIN'
    staff_list = UserProfile.objects.filter(active_company=request.user.profile.active_company)
    form = StaffAddForm(request.POST or None, company_id=request.user.profile.active_company.id)
    filter_value = request.GET.get('filter')
    if filter_value:
        if filter_value == 'All':
            pass
        else:
            staff_list = staff_list.filter(department__department__icontains=filter_value)
    if request.method == 'POST':
        if form.is_valid():
            staff_member = form.save()
            staff_member.save()
            # Redirect to the staff dashboard after successful addition
            return redirect('staff:staff_dashboard')
        else:
            # If the form is invalid, render the dashboard with the form errors
            return render(request, 'staff/staff_dashboard.html', {'form': form, 'staff_members': staff_list})
    context = {
        'staff_members': staff_list,
        'form': form,
        'is_admin': is_admin,
        'active_filter': filter_value if filter_value else 'All',
    }
    return render(request, 'staff/staff_dashboard.html', context)


# @login_required
# @require_POST
# def staff_add(request):
#     form = StaffAddForm(request.POST)
#     if form.is_valid():
#         staff_member = form.save()
#         staff_member.save()
#         return render(request, 'staff/staff_dashboard.html', {'form': StaffAddForm()})
#     else:
#         return render(request, 'staff/staff_add.html', {'form': form})


def api_staff_details(request, pk):
    if request.method == 'GET':
        try:
            staff_member = UserProfile.objects.get(id=pk)
            data = {
                'id': staff_member.id,
                'username': staff_member.user.username,
                'first_name': staff_member.user.first_name,
                'last_name': staff_member.user.last_name,
                'email': staff_member.email,
                'phone_number': staff_member.phone_number,
                'address': staff_member.address,
                'city': staff_member.city,
                'state': staff_member.state,
                'zip_code': staff_member.zip_code,
                'country': staff_member.country,
                'assigned_warehouse': staff_member.assigned_warehouse.name if staff_member.assigned_warehouse else None,
                'active_company': staff_member.active_company.name if staff_member.active_company else None,
                'assigned_role': staff_member.assigned_role,
                'department': staff_member.department.get_department_display() if staff_member.department else None,
            }
            return JsonResponse(data)
        except UserProfile.DoesNotExist:
            return JsonResponse({'error': 'Staff member not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)