from django.urls import path
from . import views
from .views import landing_page
from .views import ai_clinical_chat
app_name = 'homecare'

urlpatterns = [

    # HomeCare Dashboard
    path('homecare/', views.homecare_home, name='homecare_home'),

    #Homecare homepage
    path('', landing_page, name='home'),

    # Patients
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/create/', views.patient_create, name='patient_create'),
    path('patients/<int:pk>/update/', views.patient_update, name='patient_update'),
    path('patients/<int:pk>/delete/', views.patient_delete, name='patient_delete'),
    path('patients/<int:patient_id>/',views.patient_detail,name='patient_detail'),

    # Health Professionals
    path('professionals/', views.professional_list, name='professional_list'),
    path('professionals/create/', views.professional_create, name='professional_create'),
    path('professionals/<int:pk>/update/', views.professional_update, name='professional_update'),
    path('professionals/<int:pk>/delete/', views.professional_delete, name='professional_delete'),

    # Care Plans
    path('careplans/', views.careplan_list, name='careplan_list'),
    path('careplans/create/', views.careplan_create, name='careplan_create'),
    path('careplans/<int:pk>/update/', views.careplan_update, name='careplan_update'),
    path('careplans/<int:pk>/delete/', views.careplan_delete, name='careplan_delete'),

    # Visit Schedules
    path('visitschedules/', views.visitschedule_list, name='visitschedule_list'),
    path('visitschedules/create/', views.visitschedule_create, name='visitschedule_create'),
    path('visitschedules/<int:pk>/update/', views.visitschedule_update, name='visitschedule_update'),
    path('visitschedules/<int:pk>/delete/', views.visitschedule_delete, name='visitschedule_delete'),

    # Nurses Notes
    path('nursesnotes/', views.nursesnote_list, name='nursesnote_list'),
    path('nursesnotes/create/', views.nursesnote_create, name='nursesnote_create'),
    path('nursesnotes/<int:pk>/update/', views.nursesnote_update, name='nursesnote_update'),
    path('nursesnotes/<int:pk>/delete/', views.nursesnote_delete, name='nursesnote_delete'),

    # Doctor Notes
    path('doctornotes/', views.doctornote_list, name='doctornote_list'),
    path('doctornotes/create/', views.doctornote_create, name='doctornote_create'),
    path('doctornotes/<int:pk>/update/', views.doctornote_update, name='doctornote_update'),
    path('doctornotes/<int:pk>/delete/', views.doctornote_delete, name='doctornote_delete'),

    # Treatment Sheets
    path('treatmentsheets/', views.treatmentsheet_list, name='treatmentsheet_list'),
    path('treatmentsheets/create/', views.treatmentsheet_create, name='treatmentsheet_create'),
    path('treatmentsheets/<int:pk>/update/', views.treatmentsheet_update, name='treatmentsheet_update'),
    path('treatmentsheets/<int:pk>/delete/', views.treatmentsheet_delete, name='treatmentsheet_delete'),

    # Medication Sheets
    path('medicationsheets/', views.medicationsheet_list, name='medicationsheet_list'),
    path('medicationsheets/create/', views.medicationsheet_create, name='medicationsheet_create'),
    path('medicationsheets/<int:pk>/update/', views.medicationsheet_update, name='medicationsheet_update'),
    path('medicationsheets/<int:pk>/delete/', views.medicationsheet_delete, name='medicationsheet_delete'),

    # Vital Sign Records
    path('vitalsigns/', views.vitalsign_list, name='vitalsign_list'),
    path('vitalsigns/create/', views.vitalsign_create, name='vitalsign_create'),
    path('vitalsigns/<int:pk>/update/', views.vitalsign_update, name='vitalsign_update'),
    path('vitalsigns/<int:pk>/delete/', views.vitalsign_delete, name='vitalsign_delete'),

    #Apply for homecare services
    path("apply/", views.homecare_application, name="homecare_apply"),

    #Patient feedback and ratings on staffs and system
    path("feedback/submit/", views.submit_feedback, name="submit_feedback"),

    #Admin dashboard
    path("xadmin/dashboard/", views.admin_dashboard, name="admin_dashboard"),

    path("xadmin/patients/", views.admin_patients, name="admin_patients"),
    path("xadmin/patient/<int:patient_id>/", views.admin_patient_detail, name="admin_patient_detail"),
    path("xadmin/feedbacks/", views.admin_feedbacks, name="admin_feedbacks"),
    path("xadmin/patient/<int:patient_id>/toggle-status/",views.admin_toggle_patient_status,name="admin_toggle_patient_status"),
    path("xadmin/patient/<int:patient_id>/flag/",views.admin_flag_patient,name="admin_flag_patient"),
    path("xadmin/patient/<int:patient_id>/unflag/",views.admin_unflag_patient,name="admin_unflag_patient"),
    
    # Diagnosis
    # Diagnosis Records

    # List all diagnosis for a patient
    path("patient/<int:patient_id>/diagnosis/",views.diagnosis_list,name="diagnosis_list"),

    # Add new diagnosis for a patient
    path("patient/<int:patient_id>/diagnosis/create/",views.diagnosis_create,name="diagnosis_create"),

    # Update existing diagnosis record
    path("patient/diagnosis/<int:pk>/update/",views.diagnosis_update,name="diagnosis_update"),




    #Admin manageing staffs doctors, nurses etc.
    path("xadmin/staff/",views.admin_staff_list,name="admin_staff_list"),
    #Details
    path("xadmin/staff/<int:staff_id>/",views.admin_staff_detail,name="admin_staff_detail"),

    path("xadmin/staff/<int:staff_id>/toggle/",views.admin_toggle_staff_status,name="admin_toggle_staff_status"),

    path("xadmin/staff/<int:staff_id>/flag/",views.admin_flag_staff,name="admin_flag_staff"),

    path("xadmin/staff/<int:staff_id>/unflag/",views.admin_unflag_staff,name="admin_unflag_staff"),
    #path("ai/chat/<int:patient_id>/",ai_clinical_chat,name="ai_clinical_chat"),

        # Medication Sheets — existing routes
    path(
        "medicationsheets/",
        views.medicationsheet_list,
        name="medicationsheet_list",
    ),
    path(
        "medicationsheets/create/",
        views.medicationsheet_create,
        name="medicationsheet_create",
    ),
    path(
        "medicationsheets/<int:pk>/update/",
        views.medicationsheet_update,
        name="medicationsheet_update",
    ),
    path(
        "medicationsheets/<int:pk>/delete/",
        views.medicationsheet_delete,
        name="medicationsheet_delete",
    ),

    # Patient-centred medication management — new routes
    path(
        "patients/<int:patient_id>/medications/",
        views.patient_medications,
        name="patient_medications",
    ),
    path(
        "medications/<int:medication_id>/schedules/create/",
        views.medication_schedule_create,
        name="medication_schedule_create",
    ),
    path(
        "medications/<int:medication_id>/administrations/create/",
        views.medication_administration_create,
        name="medication_administration_create",
    ),
    path(
        "medications/<int:medication_id>/reactions/create/",
        views.medication_reaction_create,
        name="medication_reaction_create",
    ),

    path(
    "medications/<int:medication_id>/complete/",
    views.medication_mark_completed,
    name="medication_mark_completed",
),

path(
    "patients/<int:patient_id>/medications/completed/",
    views.patient_completed_medications,
    name="patient_completed_medications",
),


]
