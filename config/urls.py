from django.contrib import admin
from django.urls import path
from employees import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.login_view, name='login'),  # 🔥 ROOT FIX
    path('logout/', views.logout_view, name='logout'),

    path('admin/', admin.site.urls),

    path('hr/', views.hr_dashboard, name='hr_dashboard'),
    path('add/', views.add_employee, name='add_employee'),
    path('edit/<int:id>/', views.edit_employee, name='edit_employee'),
    path('delete/<int:id>/', views.delete_employee, name='delete_employee'),
    path('employee/', views.employee_dashboard, name='employee_dashboard'),
    path('salary/', views.all_salary, name='all_salary'),
    path('salary/my/', views.my_salary, name='my_salary'),
    path('salary/add/<int:id>/', views.add_salary, name='add_salary'),
    path('salary/delete/<int:id>/', views.delete_salary, name='delete_salary'),
    path('generate-salaries/', views.generate_salaries, name='generate_salaries'),
    path('download-payslip/<int:id>/', views.download_payslip, name='download_payslip'),
    path('hr/attendance/', views.attendance, name='hr_attendance'),
    path('hr/leaves/', views.leaves, name='hr_leaves'),
    path('mark-attendance/', views.mark_attendance, name='mark_attendance'),
    path('apply-leave/', views.apply_leave, name='apply_leave'),
    path('manage-leaves/', views.manage_leaves, name='manage_leaves'),
    path('leave/<int:id>/<str:action>/', views.update_leave, name='update_leave'),
    path('employees/', views.all_employees, name='all_employees'),
    path('terminate/<int:id>/', views.terminate_employee, name='terminate_employee'),
    path('terminated/', views.terminated_employees, name='terminated_employees'),
    path('reactivate/<int:id>/', views.reactivate_employee, name='reactivate_employee'),
    path('rfid/', views.rfid_attendance, name='rfid_attendance'),
    path('assign-rfid/<int:emp_id>/', views.assign_rfid, name='assign_rfid'),
    path('checkin-with-proof/', views.checkin_with_proof),
    path('employee-attendance/<int:id>/', views.employee_attendance, name='employee_attendance'),
    path('manager/', views.manager_dashboard, name='manager_dashboard')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)