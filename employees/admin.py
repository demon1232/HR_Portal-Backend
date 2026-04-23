from django.contrib import admin
from .models import Employee, Attendance

# Employee
admin.site.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'department', 'manager']

# Attendance
class AttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'date', 'check_in', 'status',
        'mode', 'latitude', 'longitude'
    ]

admin.site.register(Attendance, AttendanceAdmin)

