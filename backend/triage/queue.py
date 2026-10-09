from datetime import datetime, timedelta, timezone

from .models import TriageAssessment

LEVEL_RANK = {'U1': 1, 'U2': 2, 'U3': 3, 'U4': 4, 'U5': 5}
WAIT_THRESHOLDS = {'U1': 0, 'U2': 15, 'U3': 30, 'U4': 60, 'U5': 120}
DEMO_CLOCK_START = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)
_ALLOWED_CLOCK_STEPS = {15, 60}
_current_demo_time = DEMO_CLOCK_START


def _wait_minutes(assessment, now):
    return max(0, int((now - assessment.arrived_at).total_seconds() // 60))


def _aged_level(assessment, now):
    if assessment.state != TriageAssessment.State.WAITING:
        return assessment.effective_level, None
    wait = _wait_minutes(assessment, now)
    if assessment.effective_level == 'U4' and wait >= 60:
        return 'U3', 'U4'
    if assessment.effective_level == 'U5' and wait >= 60:
        return 'U4', 'U5'
    return assessment.effective_level, None


def _sort_key(row):
    aged_penalty = 1 if row['aged_from'] and row['display_level'] == 'U3' else 0
    return (
        LEVEL_RANK[row['display_level']],
        aged_penalty,
        row['arrived_at_sort'],
        row['id'],
    )


def format_queue_row(assessment, now=None):
    now = now or _current_demo_time
    display_level, aged_from = _aged_level(assessment, now)
    wait = _wait_minutes(assessment, now)
    threshold = WAIT_THRESHOLDS.get(display_level, 0)
    return {
        'id': assessment.id,
        'patient': {
            'id': assessment.patient_id,
            'reference': assessment.patient.reference,
            'full_name': assessment.patient.full_name,
        },
        'complaint': assessment.inputs.get('complaint', ''),
        'recommendation': assessment.recommendation,
        'effective_level': assessment.effective_level,
        'display_level': display_level,
        'aged_from': aged_from,
        'wait_minutes': wait,
        'needs_reassessment': wait > threshold,
        'fired_rules': assessment.fired_rules,
        'state': assessment.state,
        'arrived_at': assessment.arrived_at.isoformat(),
        'arrived_at_sort': assessment.arrived_at,
    }

def get_waiting_queue(now=None):
    now = now or _current_demo_time
    rows = []
    assessments = TriageAssessment.objects.select_related('patient').filter(
        state=TriageAssessment.State.WAITING,
    )
    for assessment in assessments:
        row = format_queue_row(assessment, now)
        rows.append(row)
    rows.sort(key=_sort_key)
    for row in rows:
        del row['arrived_at_sort']
    return rows


def advance_demo_clock(minutes):
    global _current_demo_time
    if not isinstance(minutes, int) or minutes not in _ALLOWED_CLOCK_STEPS:
        raise ValueError('Clock can only advance by 15 or 60 minutes.')
    _current_demo_time = _current_demo_time + timedelta(minutes=minutes)
    return _current_demo_time


def get_demo_clock():
    return _current_demo_time
