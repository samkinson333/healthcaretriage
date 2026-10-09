import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Patient, VitalMeasurement
from .validation import error_response, validate_patient, validate_vitals


def _parse_json(request):
    if not request.body:
        return {}, None
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return None, 'Request body must be valid JSON.'
    if not isinstance(payload, dict):
        return None, 'Request body must be a JSON object.'
    return payload, None


def patient_to_dict(patient, include_vitals=False):
    data = {
        'id': patient.id,
        'reference': patient.reference,
        'full_name': patient.full_name,
        'age': patient.age,
        'sex': patient.sex,
        'created_at': patient.created_at.isoformat(),
    }
    if include_vitals:
        data['vitals'] = [vital_to_dict(v) for v in patient.vitals.all()]
    return data


def vital_to_dict(vital):
    return {
        'id': vital.id,
        'patient_id': vital.patient_id,
        'systolic_bp': vital.systolic_bp,
        'diastolic_bp': vital.diastolic_bp,
        'pulse': vital.pulse,
        'temperature_c': float(vital.temperature_c),
        'spo2': vital.spo2,
        'source': vital.source,
        'measured_at': vital.measured_at.isoformat(),
        'created_at': vital.created_at.isoformat(),
    }


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def patients_collection(request):
    if request.method == 'GET':
        patients = Patient.objects.all()
        return JsonResponse({'patients': [patient_to_dict(p) for p in patients]})

    payload, error = _parse_json(request)
    if error:
        return JsonResponse(error_response({}, error), status=400)

    cleaned, errors = validate_patient(payload)
    if errors:
        return JsonResponse(error_response(errors), status=400)

    patient = Patient.objects.create(**cleaned)
    return JsonResponse(patient_to_dict(patient), status=201)


@require_http_methods(['GET'])
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    return JsonResponse(patient_to_dict(patient, include_vitals=True))


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def patient_vitals(request, pk):
    patient = get_object_or_404(Patient, pk=pk)

    if request.method == 'GET':
        return JsonResponse({
            'patient': patient_to_dict(patient),
            'measurements': [vital_to_dict(v) for v in patient.vitals.all()],
        })

    payload, error = _parse_json(request)
    if error:
        return JsonResponse(error_response({}, error), status=400)

    cleaned, errors = validate_vitals(payload)
    if errors:
        return JsonResponse(error_response(errors), status=400)

    vital = VitalMeasurement.objects.create(patient=patient, **cleaned)
    return JsonResponse(vital_to_dict(vital), status=201)


@require_http_methods(['GET'])
def vital_detail(request, pk):
    vital = get_object_or_404(VitalMeasurement, pk=pk)
    return JsonResponse(vital_to_dict(vital))
