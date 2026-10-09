from django.urls import path

from . import views

urlpatterns = [
    path('patients/', views.patients_collection, name='patients-collection'),
    path('patients/<int:pk>/', views.patient_detail, name='patient-detail'),
    path('patients/<int:pk>/vitals/', views.patient_vitals, name='patient-vitals'),
    path('vitals/<int:pk>/', views.vital_detail, name='vital-detail'),
    path('patients/<int:pk>/assessments/', views.patient_assessments, name='patient-assessments'),
    path('assessments/<int:pk>/', views.assessment_detail, name='assessment-detail'),
    path('demo/clock/', views.demo_clock, name='demo-clock'),
    path('queue/', views.queue_list, name='queue-list'),
    path('assessments/<int:pk>/deterioration/', views.record_deterioration, name='record-deterioration'),
]
