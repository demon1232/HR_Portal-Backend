from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db import transaction

from .models import Employee
from accounts.models import User


# 🔐 LOGIN
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            if user.is_hr:
                return redirect('hr_dashboard')
            else:
                return redirect('employee_dashboard')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'login.html')


# 🧑‍💼 HR DASHBOARD
@login_required
def hr_dashboard(request):
    if not request.user.is_hr:
        return HttpResponseForbidden()

    employees = Employee.objects.all()
    return render(request, 'hr_dashboard.html', {'employees': employees})


# 👤 EMPLOYEE DASHBOARD
@login_required
def employee_dashboard(request):
    if not request.user.is_employee:
        return HttpResponseForbidden()

    employee = get_object_or_404(Employee, user=request.user)
    return render(request, 'employee_dashboard.html', {'employee': employee})


# 🚪 LOGOUT
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# ➕ ADD EMPLOYEE
@login_required
def add_employee(request):
    if not request.user.is_hr:
        return HttpResponseForbidden()

    if request.method == 'POST':
        username = request.POST.get('username')
        department = request.POST.get('department')
        salary = request.POST.get('salary')
        joining_date = request.POST.get('joining_date')

        if not username or not joining_date:
            messages.error(request, "All fields are required")
            return redirect('add_employee')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('add_employee')

        try:
            with transaction.atomic():

                user = User.objects.create_user(
                    username=username,
                    password='12345'
                )
                user.is_employee = True
                user.save()

                Employee.objects.create(
                    user=user,
                    department=department,
                    salary=salary,
                    joining_date=joining_date
                )

            messages.success(request, "Employee added successfully")

        except Exception as e:
            print("ERROR:", e)
            messages.error(request, "Error adding employee")

        return redirect('hr_dashboard')

    return render(request, 'add_employee.html')


# ❌ DELETE EMPLOYEE
@login_required
def delete_employee(request, id):
    if not request.user.is_hr:
        return HttpResponseForbidden()

    emp = get_object_or_404(Employee, id=id)
    emp.user.delete()

    messages.success(request, "Employee deleted successfully")
    return redirect('hr_dashboard')


# ✏️ EDIT EMPLOYEE (🔥 FIXED VERSION)
@login_required
def edit_employee(request, id):
    if not request.user.is_hr:
        return HttpResponseForbidden()

    emp = get_object_or_404(Employee, id=id)

    if request.method == 'POST':
        username = request.POST.get('username')
        department = request.POST.get('department')
        salary = request.POST.get('salary')
        joining_date = request.POST.get('joining_date')

        # ✅ Username duplicate check
        if User.objects.filter(username=username).exclude(id=emp.user.id).exists():
            messages.error(request, "Username already exists")
            return redirect('edit_employee', id=id)

        try:
            with transaction.atomic():
                # 🔥 Update User (IMPORTANT)
                user = emp.user
                user.username = username
                user.save()

                # 🔥 Update Employee
                emp.department = department
                emp.salary = salary
                emp.joining_date = joining_date
                emp.save()

            messages.success(request, "Employee updated successfully")

        except Exception as e:
            print("ERROR:", e)
            messages.error(request, "Error updating employee")

        return redirect('hr_dashboard')

    return render(request, 'add_employee.html', {'employee': emp})