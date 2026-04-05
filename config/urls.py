from django.contrib import admin
from django.urls import path
from employees.views import login_view, hr_dashboard, employee_dashboard, logout_view, add_employee, delete_employee
from employees.views import edit_employee

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', login_view, name='login'),
    path('hr/', hr_dashboard, name='hr_dashboard'),
    path('employee/', employee_dashboard, name='employee_dashboard'),
    path('logout/', logout_view, name='logout'),
    path('add-employee/', add_employee, name='add_employee'),
    path('delete/<int:id>/', delete_employee, name='delete_employee'),
    path('edit/<int:id>/', edit_employee, name='edit_employee'),
]
