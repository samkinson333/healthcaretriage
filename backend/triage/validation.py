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


def error_response(errors, detail='Validation failed.'):
    return {'detail': detail, 'errors': errors}
