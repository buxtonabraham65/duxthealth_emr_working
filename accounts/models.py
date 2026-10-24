from django.db import models

class AccessRequest(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    profession = models.CharField(max_length=100)
    message = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    # models.py
    STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ]

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')


    def __str__(self):
        return self.full_name
