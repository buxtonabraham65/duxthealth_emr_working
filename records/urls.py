from django.urls import path, include
from . import views

urlpatterns = [
    path('records/', views.home, name='home'),
    path('register/', views.register_patient, name='register_patient'),
    path('patients/', views.patient_list, name='patient_list'),
    path('vitals/add/', views.add_vitals, name='add_vitals'),
    path('vitals/', views.vitals_list, name='vitals_list'),
    path('consultations/add/', views.add_consultation, name='add_consultation'),
    path('consultations/', views.consultation_list, name='consultation_list'),
    path('note/', views.note, name='note'),

    # ✅ Outreach Reports
    path('reports/outreach/detailed/', views.detailed_outreach_report, name='outreach_detailed_report'),
    path('reports/outreach/anonymous/', views.anonymous_outreach_report, name='outreach_anonymous_report'),

    # ✅ Include HomeCare app URLs under /homecare/
    #path('homecare/', include(('homecare.urls', 'homecare'), namespace='homecare')),
]
