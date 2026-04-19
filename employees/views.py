from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from django.http import HttpResponse
from decimal import Decimal
from datetime import datetime, date
from datetime import time
from .models import Leave
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
import base64
from django.core.files.base import ContentFile
import json
from django.http import JsonResponse
from geopy.distance import geodesic




from .models import Employee, SalaryRecord, Attendance
from accounts.models import User

# 🔥 ADD THIS AFTER IMPORTS (TOP PE)

def get_monthly_late(employee):
    now = datetime.now()

    total_late = Attendance.objects.filter(
        employee=employee,
        date__month=now.month,
        date__year=now.year
    ).aggregate(total=Sum('late_minutes'))['total']

    return total_late or 0


def calculate_deduction(employee):
    total_late = get_monthly_late(employee)

    allowed = 200
    per_minute_rate = employee.salary / (30 * 8 * 60)

    if total_late > allowed:
        extra = total_late - allowed
        deduction = extra * per_minute_rate
    else:
        deduction = 0

    return round(deduction, 2)

# LOGIN
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('hr_dashboard' if user.is_hr else 'employee_dashboard')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'login.html')

# EMPLOYEE DASHBOARD
@login_required
def employee_dashboard(request):

    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return HttpResponseForbidden("You are not an employee")

    # 🔥 TODAY ATTENDANCE
    attendance = Attendance.objects.filter(
        employee=employee,
        date=date.today()
    ).first()

    # 🔥 FULL HISTORY
    records = Attendance.objects.filter(
        employee=employee
    ).order_by('-date')

    # 🔥 SUMMARY
    present_count = Attendance.objects.filter(
        employee=employee, status='Present'
    ).count()

    late_count = Attendance.objects.filter(
        employee=employee, status='Late'
    ).count()

    absent_count = Attendance.objects.filter(
        employee=employee, status='Absent'
    ).count()

    # 🔥 MONTHLY LATE
    monthly_late = Attendance.objects.filter(
        employee=employee,
        date__month=date.today().month
    ).aggregate(total=Sum('late_minutes'))['total'] or 0

    # 🔥 DEDUCTION
    deduction = calculate_deduction(employee)

    # 🔥 LEAVES
    my_leaves = Leave.objects.filter(
        employee=employee
    ).order_by('-id')

    return render(request, 'employee_dashboard.html', {
        'employee': employee,
        'attendance': attendance,
        'records': records,

        'present_count': present_count,
        'late_count': late_count,
        'absent_count': absent_count,
        'monthly_late': monthly_late,
        'deduction': deduction,

        'casual': employee.casual_leaves,
        'sick': employee.sick_leaves,
        'earned': employee.earned_leaves,
        'my_leaves': my_leaves,
    })


# LOGOUT
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# ✅ ADD EMPLOYEE (FINAL FIXED)
@login_required
def add_employee(request):
    if not request.user.is_hr:
        return HttpResponseForbidden()

    if request.method == 'POST':
        username = request.POST.get('username')
        department = request.POST.get('department')
        joining_date = request.POST.get('joining_date')

        # ✅ FIXED
        profile_pic = request.FILES.get('profile_pic')

        try:
            salary = int(request.POST.get('salary'))
        except:
            messages.error(request, "Invalid salary")
            return redirect('add_employee')

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
                    joining_date=joining_date,
                    profile_pic=profile_pic   # ✅ FIXED
                )

            messages.success(request, "Employee added successfully")

        except Exception as e:
            print("ERROR:", e)
            messages.error(request, "Error adding employee")

        return redirect('hr_dashboard')

    return render(request, 'add_employee.html')


# DELETE EMPLOYEE
@login_required
def delete_employee(request, id):
    if not request.user.is_hr:
        return HttpResponseForbidden()

    emp = get_object_or_404(Employee, id=id)
    emp.user.delete()

    messages.success(request, "Employee deleted successfully")
    return redirect('hr_dashboard')


# ✅ EDIT EMPLOYEE (FINAL FIXED)
@login_required
def edit_employee(request, id):
    if not request.user.is_hr:
        return HttpResponseForbidden()

    emp = get_object_or_404(Employee, id=id)

    if request.method == 'POST':
        username = request.POST.get('username')
        department = request.POST.get('department')
        joining_date = request.POST.get('joining_date')

        # ✅ FIXED
        profile_pic = request.FILES.get('profile_pic')

        try:
            salary = int(request.POST.get('salary'))
        except:
            messages.error(request, "Invalid salary")
            return redirect('edit_employee', id=id)

        if User.objects.filter(username=username).exclude(id=emp.user.id).exists():
            messages.error(request, "Username already exists")
            return redirect('edit_employee', id=id)

        try:
            with transaction.atomic():
                user = emp.user
                user.username = username
                user.save()

                emp.department = department
                emp.salary = salary
                emp.joining_date = joining_date

                # ✅ FIXED
                if profile_pic:
                    emp.profile_pic = profile_pic

                emp.save()

            messages.success(request, "Employee updated successfully")

        except Exception as e:
            print("ERROR:", e)
            messages.error(request, "Error updating employee")

        return redirect('hr_dashboard')

    return render(request, 'add_employee.html', {'employee': emp})


# ADD SALARY
@login_required
def add_salary(request, id):
    if not request.user.is_hr:
        return HttpResponseForbidden()

    emp = get_object_or_404(Employee, id=id)

    if request.method == 'POST':
        month = request.POST.get('month')
        year = request.POST.get('year')

        try:
            total = int(request.POST.get('total'))
        except:
            messages.error(request, "Invalid amount")
            return redirect('add_salary', id=id)

        SalaryRecord.objects.create(
            employee=emp,
            month=month,
            year=year,
            total=total
        )

        messages.success(request, "Salary added successfully")
        return redirect('hr_dashboard')

    return render(request, 'add_salary.html', {'employee': emp})


# ALL SALARY
@login_required
def all_salary(request):
    if not request.user.is_hr:
        return HttpResponseForbidden()

    records = SalaryRecord.objects.all()

    name = request.GET.get('name')
    if name:
        records = records.filter(employee__user__username__icontains=name)

    month = request.GET.get('month')
    if month:
        records = records.filter(month=month)

    records = records.order_by('-year', '-month')

    return render(request, 'all_salary.html', {'records': records})


# MY SALARY
@login_required
def my_salary(request):
    if request.user.is_hr:
        return redirect('all_salary')

    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return HttpResponseForbidden()

    records = SalaryRecord.objects.filter(employee=employee)

    month = request.GET.get('month')
    year = request.GET.get('year')

    if month:
        records = records.filter(month=month)

    if year:
        records = records.filter(year=year)

    records = records.order_by('-year', '-month')

    return render(request, 'my_salary.html', {'records': records})


# GENERATE SALARIES
@login_required
def generate_salaries(request):
    if request.method == "POST":
        employees = Employee.objects.all()

        now = datetime.now()
        current_month = now.strftime("%B")
        current_year = now.year

        for emp in employees:
            SalaryRecord.objects.update_or_create(
                employee=emp,
                month=current_month,
                year=current_year,
                defaults={'total': emp.salary}
            )

        messages.success(request, "Salaries generated successfully!", extra_tags='hr')

    return redirect('hr_dashboard')


# DELETE SALARY
@login_required
def delete_salary(request, id):
    if not request.user.is_hr:
        return HttpResponseForbidden()

    record = get_object_or_404(SalaryRecord, id=id)
    record.delete()

    messages.success(request, "Salary deleted successfully", extra_tags='hr')
    return redirect('hr_dashboard')

#SALARY SLIP

@login_required
def download_payslip(request, id):
    record = get_object_or_404(SalaryRecord, id=id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Payslip_{record.employee.user.username}.pdf"'

    doc = SimpleDocTemplate(response)
    styles = getSampleStyleSheet()
    elements = []

    # 🏢 HEADER
    elements.append(Paragraph("<b><font size=16>HR PORTAL PVT LTD</font></b>", styles['Title']))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph("<font size=10>Lahore, Pakistan</font>", styles['Normal']))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("<b><font size=14>Salary Payslip</font></b>", styles['Heading2']))
    elements.append(Spacer(1, 20))

    # 👤 INFO
    info_data = [
        ["Employee", record.employee.user.username],
        ["Department", record.employee.department],
        ["Month", f"{record.month} {record.year}"],
        ["Issue Date", str(datetime.now().date())],
        ["Payslip ID", str(record.id)],
    ]

    info_table = Table(info_data, colWidths=[120, 200])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(info_table)
    elements.append(Spacer(1, 20))

    # 💰 CALCULATIONS (FINAL)
    basic = record.total * Decimal('0.7')
    house = record.total * Decimal('0.15')
    medical = record.total * Decimal('0.10')
    other = record.total * Decimal('0.05')

    gross = basic + house + medical + other

    eobi = Decimal('1000')
    pf = basic * Decimal('0.05')
    tax = record.total * Decimal('0.05')

    late_deduction = Decimal(str(calculate_deduction(record.employee)))

    total_deduction = eobi + pf + tax + late_deduction
    net = gross - total_deduction

    # 📊 TABLE
    data = [
        ["Earnings", "Amount", "Deductions", "Amount"],

        ["Basic Salary", f"Rs {round(basic,2)}", "EOBI", f"Rs {round(eobi,2)}"],
        ["House Allowance", f"Rs {round(house,2)}", "Provident Fund", f"Rs {round(pf,2)}"],
        ["Medical Allowance", f"Rs {round(medical,2)}", "Tax", f"Rs {round(tax,2)}"],
        ["Other Allowance", f"Rs {round(other,2)}", "Late Deduction", f"Rs {round(late_deduction,2)}"],

        ["Gross Salary", f"Rs {round(gross,2)}", "Total Deduction", f"Rs {round(total_deduction,2)}"],
        ["Net Salary", f"Rs {round(net,2)}", "", ""],
    ]

    table = Table(data, colWidths=[140, 100, 140, 100])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1a237e")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),

        ('BACKGROUND', (0, 5), (1, 5), colors.lightgrey),
        ('BACKGROUND', (0, 6), (1, 6), colors.yellow),
        ('FONTNAME', (0, 6), (1, 6), 'Helvetica-Bold'),
    ]))

    # 🚨 MOST IMPORTANT FIX
    elements.append(table)

    # ✍️ FOOTER
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("Authorized Signature", styles['Normal']))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("_________________________", styles['Normal']))

    doc.build(elements)
    return response


@login_required
def approve_leave(request, id):
    leave = get_object_or_404(Leave, id=id)
    leave.status = 'Approved'
    leave.save()
    return redirect('all_leaves')

@login_required
def attendance(request):
    return render(request, 'hr_attendance.html')


@login_required
def leaves(request):
    return render(request, 'hr_leaves.html')

    

@login_required
def mark_attendance(request):
    emp = Employee.objects.get(user=request.user)
    today = date.today()

    attendance, created = Attendance.objects.get_or_create(
        employee=emp,
        date=today
    )

    attendance.source = 'web'
    
    action = request.POST.get('action')
    office_time = time(9, 0)

    # ✅ CHECK-IN
    if action == 'checkin':

        if attendance.check_in:
            messages.warning(request, "Already checked in!", extra_tags='employee')
            return redirect('employee_dashboard')

        now_time = datetime.now().time()
        attendance.check_in = now_time

        # 🔥 LATE CALCULATION
        if now_time > office_time:
            late = datetime.combine(today, now_time) - datetime.combine(today, office_time)
            attendance.late_minutes = int(late.total_seconds() / 60)
            attendance.status = 'Late'
        else:
            attendance.status = 'Present'

        attendance.save()
        messages.success(request, "Check-in successful!", extra_tags='employee')


    # ✅ CHECK-OUT
    elif action == 'checkout':

        if not attendance.check_in:
            messages.warning(request, "Check-in first!", extra_tags='employee')
            return redirect('employee_dashboard')

        if attendance.check_out:
            messages.warning(request, "Already checked out!", extra_tags='employee')
            return redirect('employee_dashboard')

        attendance.check_out = datetime.now().time()
        attendance.save()
        messages.success(request, "Check-out successful!", extra_tags='employee')

    return redirect('employee_dashboard')

    from django.db.models import Sum
from datetime import datetime

def get_monthly_late(employee):
    now = datetime.now()

    total_late = Attendance.objects.filter(
        employee=employee,
        date__month=now.month,
        date__year=now.year
    ).aggregate(total=Sum('late_minutes'))['total']

    return total_late or 0


@login_required
def apply_leave(request):
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return HttpResponseForbidden("You are not an employee")

    if request.method == 'POST':
        leave_type = request.POST['leave_type']

        # 🔥 HOURLY LEAVE (FROM TIME → TO TIME)
        if leave_type == "hourly":
            from_time = request.POST.get('from_time')
            to_time = request.POST.get('to_time')

            if not from_time or not to_time:
                return HttpResponse("Please select both times")

            t1 = datetime.strptime(from_time, "%H:%M")
            t2 = datetime.strptime(to_time, "%H:%M")

            if t2 <= t1:
                return HttpResponse("Invalid time range")

            # 🔥 CALCULATE HOURS
            diff = t2 - t1
            hours = diff.seconds / 3600

            Leave.objects.create(
                employee=employee,
                leave_type="Hourly",
                hours=hours,
                reason=request.POST['reason']
            )

        else:
            start_date = datetime.strptime(request.POST['start_date'], "%Y-%m-%d").date()
            end_date = datetime.strptime(request.POST['end_date'], "%Y-%m-%d").date()

            if end_date < start_date:
                return HttpResponse("Invalid date range")

            Leave.objects.create(
                employee=employee,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                reason=request.POST['reason']
            )

        return redirect('employee_dashboard')

    return render(request, 'apply_leave.html')

@login_required
def manage_leaves(request):
    if not request.user.is_hr:
        return HttpResponseForbidden()

    leaves = Leave.objects.all().order_by('-id')

    return render(request, 'manage_leaves.html', {
        'leaves': leaves
    })


@login_required
def update_leave(request, id, action):
    if not request.user.is_hr:
        return HttpResponseForbidden()

    leave = get_object_or_404(Leave, id=id)
    employee = leave.employee

    if action == 'approve':
        leave.status = 'Approved'

        # 🔥 HOURLY LEAVE
        if leave.leave_type == "Hourly":
            hours = leave.hours or 0
            total_minutes = int(hours * 60)

            # 🔥 GET MONTHLY LATE
            current_late = get_monthly_late(employee)

            # limit (exploit prevent)
            if total_minutes > current_late:
                total_minutes = current_late

            # 🔥 REDUCE LATE MINUTES FROM ATTENDANCE
            remaining = total_minutes

            attendances = Attendance.objects.filter(
                employee=employee,
                date__month=datetime.now().month,
                date__year=datetime.now().year,
                late_minutes__gt=0
            ).order_by('date')

            for att in attendances:
                if remaining <= 0:
                    break

                if att.late_minutes <= remaining:
                    remaining -= att.late_minutes
                    att.late_minutes = 0
                else:
                    att.late_minutes -= remaining
                    remaining = 0

                att.save()

        # 🔥 FULL DAY LEAVE
        else:
            total_days = (leave.end_date - leave.start_date).days + 1

            if leave.leave_type == "Casual":
                employee.casual_leaves -= total_days

            elif leave.leave_type == "Sick":
                employee.sick_leaves -= total_days

            elif leave.leave_type == "Earned":
                employee.earned_leaves -= total_days

            employee.save()

    elif action == 'reject':
        leave.status = 'Rejected'

    leave.save()

    return redirect('manage_leaves')

@login_required
def hr_dashboard(request):
    if not request.user.is_hr:
        return HttpResponseForbidden()
    
    mark_absent_for_today()

    employees = Employee.objects.all()
    total_salary = employees.aggregate(total=Sum('salary'))['total'] or 0

    # 🔥 ANALYTICS
    total_employees = employees.count()

    total_late = Attendance.objects.aggregate(
        total=Sum('late_minutes')
    )['total'] or 0

    total_leaves = Leave.objects.count()

    return render(request, 'hr_dashboard.html', {
        'employees': employees,
        'total_salary': total_salary,

        # 🔥 NEW DATA
        'total_employees': total_employees,
        'total_late': total_late,
        'total_leaves': total_leaves,
    })

def all_employees(request):
    employees = Employee.objects.filter(is_active=True)
    return render(request, 'all_employees.html', {'employees': employees})

def terminate_employee(request, id):
    employee = get_object_or_404(Employee, id=id)
    employee.is_active = False
    employee.save()
    return redirect('all_employees')

def terminated_employees(request):
    employees = Employee.objects.filter(is_active=False)
    return render(request, 'employees/terminated_employees.html', {'employees': employees})

def reactivate_employee(request, id):
    employee = get_object_or_404(Employee, id=id)
    employee.is_active = True
    employee.save()
    return redirect('terminated_employees')

from datetime import date
from .models import Employee, Attendance

def mark_absent_for_today():
    today = date.today()

    for emp in Employee.objects.filter(is_active=True):
        exists = Attendance.objects.filter(employee=emp, date=today).exists()

        if not exists:
            Attendance.objects.create(
                employee=emp,
                date=today,
                status="Absent"
            )

@login_required
def assign_rfid(request, emp_id):
    employee = Employee.objects.get(id=emp_id)

    if request.method == "POST":
        rfid = request.POST.get("rfid")

        # Duplicate check
        if Employee.objects.filter(rfid=rfid).exists():
            messages.error(request, "Card already assigned")
        else:
            employee.rfid = rfid
            employee.save()
            messages.success(request, "RFID assigned successfully")

    return render(request, "employees/assign_rfid.html", {"employee": employee})

def rfid_attendance(request):
    if request.method == "POST":
        rfid = request.POST.get("rfid")

        try:
            employee = Employee.objects.get(rfid=rfid)
        except Employee.DoesNotExist:
            messages.error(request, "Invalid Card ❌")
            return redirect("rfid_attendance")

        today = date.today()

        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=today
        )

        attendance.source = 'rfid'

        # 🔥 LOGIC START
        if not attendance.check_in:
            attendance.check_in = timezone.now().time()
            attendance.save()
            messages.success(request, f"{employee.full_name} Checked In ✅")

        elif not attendance.check_out:
            attendance.check_out = timezone.now().time()
            attendance.save()
            messages.success(request, f"{employee.full_name} Checked Out ⏱️")

        else:
            messages.warning(request, "Already completed attendance ⚠️")

        return redirect("rfid_attendance")

    return render(request, "employees/rfid_attendance.html")

@csrf_exempt
def rfid_api(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request"})

    rfid = request.POST.get("rfid")

    try:
        employee = Employee.objects.get(rfid=rfid)
    except Employee.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Invalid card"})

    today = timezone.localdate()
    now = timezone.localtime()
    current_time = now.time()

    attendance, created = Attendance.objects.get_or_create(
        employee=employee,
        date=today
    )

    attendance.source = "rfid"

    office_time = time(9, 0)

    # 🔥 CHECK-IN
    if not attendance.check_in:
        attendance.check_in = current_time

        if current_time > office_time:
            late = datetime.combine(today, current_time) - datetime.combine(today, office_time)
            attendance.late_minutes = int(late.total_seconds() / 60)
            attendance.status = "Late"
        else:
            attendance.status = "Present"

        action = "check-in"

    # 🔥 CHECK-OUT
    elif not attendance.check_out:
        attendance.check_out = current_time
        action = "check-out"

    else:
        return JsonResponse({
            "status": "ignored",
            "message": "Already marked"
        })

    attendance.save()

    return JsonResponse({
        "status": "success",
        "action": action,
        "employee": employee.full_name
    })

@login_required
def checkin_with_proof(request):
    try:
        if request.method == "POST":

            data = json.loads(request.body)

            image_data = data.get('image')
            lat = data.get('lat')
            lng = data.get('lng')

            print("LAT:", lat, "LNG:", lng)

            # ✅ Location validation
            if lat is None or lng is None:
                return JsonResponse({
                    "status": "error",
                    "message": "Location not received ❌"
                })

            lat = float(lat)
            lng = float(lng)

            # ✅ Image validation
            if not image_data:
                return JsonResponse({
                    "status": "error",
                    "message": "No image received"
                })

            # ✅ Decode image
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]
            file = ContentFile(base64.b64decode(imgstr), name=f'selfie.{ext}')

            # ✅ Get employee
            employee = Employee.objects.get(user=request.user)

            attendance, created = Attendance.objects.get_or_create(
                employee=employee,
                date=timezone.localdate()
            )

            if attendance.check_in:
                return JsonResponse({
                    "status": "error",
                    "message": "Already checked in"
                })

            # ✅ Save selfie
            attendance.selfie = file
            attendance.save()

            # ✅ Face verification
            if not employee.face_image:
                attendance.selfie = None
                attendance.save()
                return JsonResponse({
                    "status": "error",
                    "message": "No registered face found"
                })

            known_image = face_recognition.load_image_file(employee.face_image.path)
            unknown_image = face_recognition.load_image_file(attendance.selfie.path)

            known_encodings = face_recognition.face_encodings(known_image)
            unknown_encodings = face_recognition.face_encodings(unknown_image)

            if not known_encodings or not unknown_encodings:
                attendance.selfie = None
                attendance.save()
                return JsonResponse({
                    "status": "error",
                    "message": "Face not detected ❌"
                })

            face_distance = face_recognition.face_distance(
                [known_encodings[0]],
                unknown_encodings[0]
            )[0]

            print("Face Distance:", face_distance)

            if face_distance > 0.5:
                attendance.selfie = None
                attendance.save()
                return JsonResponse({
                    "status": "error",
                    "message": "Face not matched ❌"
                })

            # ✅ Save attendance
            attendance.latitude = lat
            attendance.longitude = lng
            attendance.check_in = timezone.now().time()
            attendance.source = 'web'

            # ✅ 🔥 ADD THIS (MAP LINK)
            attendance.map_link = f"https://www.google.com/maps?q={lat},{lng}"

            # ✅ Office detection
            office = (31.556833, 74.300250)
            employee_loc = (lat, lng)

            geo_distance = geodesic(office, employee_loc).meters

            if geo_distance <= 100:
                attendance.status = "Office"
            else:
                attendance.status = "Outside"

            attendance.save()

            return JsonResponse({"status": "success"})

        return JsonResponse({
            "status": "error",
            "message": "Invalid request"
        })

    except Exception as e:
        print("ERROR:", str(e))
        return JsonResponse({
            "status": "error",
            "message": str(e)
        })
    
def employee_attendance(request, id):
    employee = Employee.objects.get(id=id)

    records = Attendance.objects.filter(
        employee=employee
    ).order_by('-date')

    return render(request, 'employee_attendance.html', {
        'employee': employee,
        'records': records
    })