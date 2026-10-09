import json

from django.http import JsonResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .assessment import assess
from .models import Patient, TriageAssessment, VitalMeasurement, QueueEvent
from .queue import advance_demo_clock, get_waiting_queue, format_queue_row, LEVEL_RANK
from .validation import error_response, validate_assessment, validate_patient, validate_vitals


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


def assessment_to_dict(assessment):
    return {
        'id': assessment.id,
        'patient': patient_to_dict(assessment.patient),
        'inputs': assessment.inputs,
        'recommendation': assessment.recommendation,
        'effective_level': assessment.effective_level,
        'fired_rules': assessment.fired_rules,
        'news2_breakdown': assessment.news2_breakdown,
        'warnings': assessment.warnings,
        'direct_clinician_assessment': bool(
            assessment.inputs.get('direct_clinician_assessment', False)
        ),
        'rule_version': assessment.rule_version,
        'state': assessment.state,
        'arrived_at': assessment.arrived_at.isoformat(),
        'created_at': assessment.created_at.isoformat(),
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


@csrf_exempt
@require_http_methods(['POST'])
def patient_assessments(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    payload, error = _parse_json(request)
    if error:
        return JsonResponse(error_response({}, error), status=400)

    cleaned, errors = validate_assessment(payload)
    if errors:
        return JsonResponse(error_response(errors), status=400)

    result = assess(cleaned)
    assessment_inputs = {
        **cleaned,
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
    return JsonResponse(assessment_to_dict(assessment), status=201)


@require_http_methods(['GET'])
def assessment_detail(request, pk):
    assessment = get_object_or_404(TriageAssessment, pk=pk)
    return JsonResponse(assessment_to_dict(assessment))


@csrf_exempt
@require_http_methods(['POST'])
def demo_clock(request):
    payload, error = _parse_json(request)
    if error:
        return JsonResponse(error_response({}, error), status=400)
    minutes = payload.get('minutes')
    if not isinstance(minutes, int):
        return JsonResponse(error_response({'minutes': 'Must be an integer.'}), status=400)
    try:
        new_clock = advance_demo_clock(minutes)
    except ValueError as e:
        return JsonResponse(error_response({'minutes': str(e)}), status=400)
    return JsonResponse({'clock': new_clock.isoformat()}, status=200)


@require_http_methods(['GET'])
def queue_list(request):
    return JsonResponse({'queue': get_waiting_queue()})


@csrf_exempt
@require_http_methods(['POST'])
def record_deterioration(request, pk):
    payload, _ = _parse_json(request)
    request_id = payload.get('request_id') if payload else None

    with transaction.atomic():
        assessment = get_object_or_404(TriageAssessment.objects.select_for_update(), pk=pk)

        if assessment.state != TriageAssessment.State.WAITING:
            return JsonResponse({'error': 'Only waiting patients can deteriorate.'}, status=400)

        if request_id:
            # Check for idempotency
            recent_event = QueueEvent.objects.filter(
                assessment=assessment,
                event_type=QueueEvent.EventType.DETERIORATION,
                reason__contains=request_id
            ).exists()
            if recent_event:
                return JsonResponse(format_queue_row(assessment))

        current_level = assessment.effective_level
        current_rank = LEVEL_RANK[current_level]
        if current_rank <= 1:
            return JsonResponse({'error': 'Cannot escalate beyond U1.'}, status=400)

        new_rank = current_rank - 1
        new_level = [k for k, v in LEVEL_RANK.items() if v == new_rank][0]

        before_snapshot = {'effective_level': current_level}
        after_snapshot = {'effective_level': new_level}

        assessment.effective_level = new_level
        assessment.save(update_fields=['effective_level'])

        reason = 'Recorded deterioration'
        if request_id:
            reason += f' [req:{request_id}]'

        QueueEvent.objects.create(
            assessment=assessment,
            event_type=QueueEvent.EventType.DETERIORATION,
            before=before_snapshot,
            after=after_snapshot,
            reason=reason,
            occurred_at=timezone.now(),
        )

    return JsonResponse(format_queue_row(assessment))
