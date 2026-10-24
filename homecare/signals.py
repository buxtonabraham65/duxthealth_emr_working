# homecare/signals.py
#from django.db.models.signals import post_save
#from django.dispatch import receiver
#from django.contrib.auth import get_user_model
#from django.utils import timezone
#from .models import Patient

#User = get_user_model()

#@receiver(post_save, sender=User)
#def create_patient_profile(sender, instance, created, **kwargs):
#    if created:
#        Patient.objects.create(
#            user=instance,
#            first_name=instance.first_name or "Patient",
#            last_name=instance.last_name or "",
#            gender="O",
#            contact_phone="",
#            address="",
#            date_of_birth="2000-01-01",
#            created_at=timezone.now(),
#        )
