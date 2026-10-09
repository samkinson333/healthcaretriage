"""Validation helpers for patient registration and vital-sign measurements.

Ranges are prototype assumptions, not clinical protocols. Missing or implausible
values are rejected rather than silently treated as normal.
"""
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Patient, VitalMeasurement

VITAL_RANGES = {
    'systolic_bp': (50, 300),
    'diastolic_bp': (20, 200),
    'pulse': (20, 250),
    'temperature_c': (25.0, 45.0),
    'spo2': (50, 100),
}

ASSESSMENT_OBSERVATION_RANGES = {
    'respiratory_rate': (3, 60, int),
    'spo2': (50, 100, int),
    'temperature_c': (25.0, 45.0, float),
    'systolic_bp': (50, 300, int),
    'pulse': (20, 250, int),
}

ASSESSMENT_REQUIRED_OBSERVATIONS = [
    'respiratory_rate',
    'spo2',
    'supplemental_oxygen',
    'temperature_c',
    'systolic_bp',
    'pulse',
    'consciousness',
]

ASSESSMENT_SOURCES = {'manual', 'device'}
ASSESSMENT_CONSCIOUSNESS = {'alert', 'confusion', 'voice', 'pain', 'unresponsive'}
ASSESSMENT_SPO2_SCALES = {1, 2}
ASSESSMENT_SYMPTOMS = {
    'unresponsive',
    'airway_compromise',
    'active_seizure',
    'severe_bleeding',
    'anaphylaxis',
    'chest_pain',
    'stroke_signs',
    'severe_breathlessness',
    'vomiting_blood',
}


def _as_int(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        text = str(value).strip()
        if text == '':
            return None
        return int(text)
    except (TypeError, ValueError):
        return None


def _as_float(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        text = str(value).strip()
        if text == '':
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def validate_patient(data):
    """Validate a patient registration payload.

    Returns (cleaned, errors). ``cleaned`` is only meaningful when errors is empty.
    """
    errors = {}
    cleaned = {}

    full_name = str(data.get('full_name', '')).strip()
    if len(full_name) > 150:
        errors['full_name'] = 'Name must be 150 characters or fewer.'
    cleaned['full_name'] = full_name

    age = _as_int(data.get('age'))
    if age is None:
        errors['age'] = 'Age is required and must be a whole number.'
    elif not 0 <= age <= 120:
        errors['age'] = 'Age must be between 0 and 120.'
    else:
        cleaned['age'] = age

    sex = str(data.get('sex', '')).strip().lower() or Patient.Sex.OTHER
    if sex not in Patient.Sex.values:
        errors['sex'] = f"Sex must be one of: {', '.join(Patient.Sex.values)}."
    else:
        cleaned['sex'] = sex

    return cleaned, errors


def validate_vitals(data):
    """Validate a vital-sign measurement payload.

    Returns (cleaned, errors). Every numeric field is required; implausible
    values are rejected with a field-level message.
    """
    errors = {}
    cleaned = {}
    parsed = {}

    for field, (low, high) in VITAL_RANGES.items():
        raw = data.get(field)
        if raw is None or str(raw).strip() == '':
            errors[field] = 'This measurement is required.'
            continue
        if field == 'temperature_c':
            value = _as_float(raw)
        else:
            value = _as_int(raw)
        if value is None:
            errors[field] = 'Enter a valid number.'
            continue
        if not low <= value <= high:
            errors[field] = f'Value must be between {low} and {high}.'
            continue
        parsed[field] = value
        cleaned[field] = value

    systolic = parsed.get('systolic_bp')
    diastolic = parsed.get('diastolic_bp')
    if systolic is not None and diastolic is not None and systolic <= diastolic:
        errors['systolic_bp'] = 'Systolic pressure must be higher than diastolic.'

    source = str(data.get('source', '')).strip().lower() or VitalMeasurement.Source.MANUAL
    if source not in VitalMeasurement.Source.values:
        errors['source'] = f"Source must be one of: {', '.join(VitalMeasurement.Source.values)}."
    else:
        cleaned['source'] = source

    measured_at_raw = data.get('measured_at')
    if measured_at_raw in (None, ''):
        cleaned['measured_at'] = timezone.now()
    else:
        measured_at = parse_datetime(str(measured_at_raw))
        if measured_at is None:
            errors['measured_at'] = 'Enter a valid ISO 8601 timestamp.'
        else:
            if timezone.is_naive(measured_at):
                measured_at = timezone.make_aware(measured_at, timezone.get_current_timezone())
            cleaned['measured_at'] = measured_at

    return cleaned, errors


def validate_assessment(data):
    errors = {}
    cleaned = {
        'observations': {},
        'sources': {},
        'symptoms': [],
    }

    if not isinstance(data, dict):
        return {}, {'payload': 'Request body must be a JSON object.'}

    age = _as_int(data.get('age'))
    if age is None:
        errors['age'] = 'Age is required and must be a whole number.'
    elif not 0 <= age <= 120:
        errors['age'] = 'Age must be between 0 and 120.'
    else:
        cleaned['age'] = age

    pregnant = data.get('pregnant', False)
    if not isinstance(pregnant, bool):
        errors['pregnant'] = 'Pregnant must be true or false.'
    else:
        cleaned['pregnant'] = pregnant

    nurse_concern = data.get('nurse_concern', False)
    if not isinstance(nurse_concern, bool):
        errors['nurse_concern'] = 'Nurse concern must be true or false.'
    else:
        cleaned['nurse_concern'] = nurse_concern

    spo2_scale = data.get('spo2_scale', 1)
    if isinstance(spo2_scale, bool) or spo2_scale not in ASSESSMENT_SPO2_SCALES:
        errors['spo2_scale'] = 'SpO2 scale must be 1 or 2.'
    else:
        cleaned['spo2_scale'] = spo2_scale

    raw_symptoms = data.get('symptoms', [])
    if not isinstance(raw_symptoms, list):
        errors['symptoms'] = 'Symptoms must be a list.'
    else:
        normalized_symptoms = []
        invalid = []
        for item in raw_symptoms:
            symptom = str(item).strip().lower()
            if symptom not in ASSESSMENT_SYMPTOMS:
                invalid.append(symptom or '<blank>')
            elif symptom not in normalized_symptoms:
                normalized_symptoms.append(symptom)
        if invalid:
            errors['symptoms'] = f"Unknown symptoms: {', '.join(invalid)}."
        else:
            cleaned['symptoms'] = normalized_symptoms

    observations = data.get('observations')
    if not isinstance(observations, dict):
        errors['observations'] = 'Observations must be an object.'
        return cleaned, errors

    for field in ASSESSMENT_REQUIRED_OBSERVATIONS:
        raw_entry = observations.get(field, {'value': None, 'source': 'manual'})
        if raw_entry is None:
            raw_entry = {'value': None, 'source': 'manual'}
        if not isinstance(raw_entry, dict):
            errors[f'observations.{field}'] = 'Observation must be an object with value and source.'
            continue

        source = str(raw_entry.get('source', 'manual')).strip().lower() or 'manual'
        if source not in ASSESSMENT_SOURCES:
            errors[f'observations.{field}.source'] = "Source must be one of: manual, device."
        else:
            cleaned['sources'][field] = source

        raw_value = raw_entry.get('value')
        if raw_value is None or (isinstance(raw_value, str) and raw_value.strip() == ''):
            cleaned['observations'][field] = None
            continue

        if field == 'supplemental_oxygen':
            if not isinstance(raw_value, bool):
                errors[f'observations.{field}'] = 'Supplemental oxygen must be true, false, or missing.'
            else:
                cleaned['observations'][field] = raw_value
            continue

        if field == 'consciousness':
            value = str(raw_value).strip().lower()
            if value not in ASSESSMENT_CONSCIOUSNESS:
                errors[f'observations.{field}'] = (
                    'Consciousness must be one of: alert, confusion, voice, pain, unresponsive.'
                )
            else:
                cleaned['observations'][field] = value
            continue

        low, high, kind = ASSESSMENT_OBSERVATION_RANGES[field]
        if isinstance(raw_value, bool):
            errors[f'observations.{field}'] = 'Enter a valid number.'
            continue
        value = _as_float(raw_value) if kind is float else _as_int(raw_value)
        if value is None:
            errors[f'observations.{field}'] = 'Enter a valid number or leave missing.'
            continue
        if not low <= value <= high:
            errors[f'observations.{field}'] = f'Value must be between {low} and {high}.'
            continue
        cleaned['observations'][field] = value

    complaint = str(data.get('complaint', '')).strip()
    if len(complaint) > 500:
        errors['complaint'] = 'Complaint must be 500 characters or fewer.'
    cleaned['complaint'] = complaint

    return cleaned, errors


def error_response(errors, detail='Validation failed.'):
    return {'detail': detail, 'errors': errors}
