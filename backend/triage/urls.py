from django.urls import path

from . import views

urlpatterns = [
    path('patients/', views.patients_collection, name='patients-collection'),
    path('patients/<int:pk>/', views.patient_detail, name='patient-detail'),
    path('patients/<int:pk>/vitals/', views.patient_vitals, name='patient-vitals'),
    path('vitals/<int:pk>/', views.vital_detail, name='vital-detail'),
]
