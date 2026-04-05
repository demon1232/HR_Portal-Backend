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

    def __str__(self):
        return self.full_name