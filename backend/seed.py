import os
import sys
import django
from django.utils import timezone

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from triage.models import Patient, TriageAssessment
from triage.assessment import assess

patients_data = [
    {
        'patient': {'full_name': 'John Doe', 'age': 35, 'sex': 'male'},
        'observations': {
            'respiratory_rate': 16,
            'spo2': 98,
            'supplemental_oxygen': False,
            'temperature_c': 37.0,
            'systolic_bp': 120,
            'pulse': 70,
            'consciousness': 'alert',
        },
        'symptoms': [],
        'nurse_concern': False,
    },
    {
        'patient': {'full_name': 'Jane Smith', 'age': 42, 'sex': 'female'},
        'observations': {
            'respiratory_rate': 16,
            'spo2': 91,
            'supplemental_oxygen': False,
            'temperature_c': 37.0,
            'systolic_bp': 120,
            'pulse': 70,
            'consciousness': 'alert',
        },
        'symptoms': [],
        'nurse_concern': False,
    },
    {
        'patient': {'full_name': 'Robert Jones', 'age': 65, 'sex': 'male'},
        'observations': {
            'respiratory_rate': 28,
            'spo2': 89,
            'supplemental_oxygen': True,
            'temperature_c': 39.5,
            'systolic_bp': 85,
            'pulse': 135,
            'consciousness': 'confusion',
        },
        'symptoms': [],
        'nurse_concern': False,
    }
]

for data in patients_data:
    patient = Patient.objects.create(**data['patient'])
    inputs = {
        'observations': data['observations'],
        'symptoms': data['symptoms'],
        'age': data['patient']['age'],
        'pregnant': False,
        'nurse_concern': data['nurse_concern'],
    }
    
    result = assess(inputs)
    assessment_inputs = {
        **inputs,
        'direct_clinician_assessment': result['direct_clinician_assessment'],
    }
    
    assessment = TriageAssessment.objects.create(
        patient=patient,
        inputs=assessment_inputs,
        recommendation=result['recommendation'],
        effective_level=result['recommendation'],
        fired_rules=result['fired_rules'],
        news2_breakdown=result['news2_breakdown'],
        warnings=result['warnings'],
        rule_version=result['rule_version'],
        state=TriageAssessment.State.WAITING,
        arrived_at=timezone.now(),
    )
    print(f"Created Patient: {patient.full_name} | Urgency: {assessment.effective_level} | Fired rules: {[r['id'] for r in result['fired_rules']]}")

print("Successfully seeded patients!")
