from django.db import models
from django.contrib.auth.models import User

class Outreach(models.Model):
    location = models.CharField(max_length=200)
    date = models.DateField()
    team = models.TextField(help_text="Names of volunteers or staff")
    summary = models.TextField(blank = True, null = True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.location} - {self.date.strftime('%Y-%m-%d')}"

class Patient(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    full_name = models.CharField(max_length=100)
    dob = models.DateField(verbose_name="Date of Birth")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    community = models.CharField(max_length=100)
    allergies = models.TextField(blank=True)
    medical_history = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date_registered = models.DateTimeField(auto_now_add=True)
    outreach = models.ForeignKey(Outreach, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.full_name

class VitalSign(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    bp_systolic = models.IntegerField(blank=True, null=True, verbose_name="Systolic BP")
    bp_diastolic = models.IntegerField(blank=True, null=True, verbose_name="Diastolic BP")
    temp_c = models.FloatField(blank=True, null=True, verbose_name="Temperature (°C)")
    heart_rate = models.IntegerField(blank=True, null=True)
    spo2 = models.IntegerField(blank=True, null=True, verbose_name="SpO₂ (%)")
    glucose = models.FloatField(blank=True, null=True, verbose_name="Glucose (mmol/L)")
    weight = models.FloatField(blank=True, null=True, help_text="In kilograms")
    height = models.FloatField(blank=True, null=True, help_text="In centimeters")
    bmi = models.FloatField(blank=True, null=True, help_text="Auto-calculated")
    date_recorded = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    outreach = models.ForeignKey(Outreach, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.height and self.weight:
            self.bmi = round(self.weight / ((self.height / 100) ** 2), 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Vitals for {self.patient.full_name} on {self.date_recorded.strftime('%Y-%m-%d')}"

class Consultation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    notes = models.TextField()
    diagnosis = models.TextField()
    prescription = models.TextField(blank=True)
    referred_to = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    outreach = models.ForeignKey(Outreach, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Consultation for {self.patient.full_name} on {self.created_at.strftime('%Y-%m-%d')}"

class Note(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    diagnosis = models.CharField(max_length=500, null=True, blank=True)
    notes = models.TextField()
    referred_to = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consultation for {self.patient.full_name} on {self.created_at.strftime('%Y-%m-%d')}"
