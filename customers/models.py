from django.conf import settings
from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)  # Optional name field
    customer_code = models.CharField(max_length=100, unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    company = models.ForeignKey('users.Company', on_delete=models.CASCADE, related_name='customers')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # zapisz najpierw → dostajemy pk
        if not self.customer_code:
            self.customer_code = f"CUST-{self.pk}"
            Customer.objects.filter(pk=self.pk).update(customer_code=self.customer_code)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"