from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Employee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    department = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    salary = models.IntegerField()
    joining_date = models.DateField()
    profile_pic = models.ImageField(upload_to='profiles/', null=True, blank=True)
    role = models.CharField(max_length=50, default='Employee')
    casual_leaves = models.IntegerField(default=14)
    sick_leaves = models.IntegerField(default=8)
    earned_leaves = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)
    rfid = models.CharField(max_length=100, unique=True, null=True, blank=True)
    face_image = models.ImageField(upload_to='faces/', null=True, blank=True)


    def __str__(self):
        return self.full_name


class SalaryRecord(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.CharField(max_length=20)
    year = models.IntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('employee', 'month', 'year')

    def __str__(self):
        return f"{self.employee.full_name} - {self.month} {self.year}"
    
class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    
    date = models.DateField(auto_now_add=True)
    
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)

    SOURCE_CHOICES = [
        ('web', 'Web'),
        ('rfid', 'RFID'),
    ]

    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='web')

    late_minutes = models.IntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=[
            ('Present', 'Present'),
            ('Absent', 'Absent'),
            ('Late', 'Late'),
        ],
        default='Present'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # 🔥 YEH ADD KARNA HAI
    updated_at = models.DateTimeField(auto_now=True)

    selfie = models.ImageField(upload_to='attendance_selfies/', null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    map_link = models.URLField(null=True, blank=True)



    class Meta:
        unique_together = ['employee', 'date']

    def __str__(self):
        return f"{self.employee.user.username} - {self.date}"


class Leave(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    
    LEAVE_TYPES = [
        ('Casual', 'Casual'),
        ('Sick', 'Sick'),
        ('Annual', 'Annual'),
        ('Earned', 'Earned'),
    ]

    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    hours = models.IntegerField(null=True, blank=True)

    status = models.CharField(max_length=20, default='Pending', choices=[
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ])

    def __str__(self):
        return f"{self.employee.user.username} - {self.leave_type}"
