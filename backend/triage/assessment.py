RULE_VERSION = 'prototype-1'

LEVEL_RANK = {'U1': 1, 'U2': 2, 'U3': 3, 'U4': 4, 'U5': 5}

REQUIRED_OBSERVATIONS = [
    'respiratory_rate',
    'spo2',
    'supplemental_oxygen',
    'temperature_c',
    'systolic_bp',
    'pulse',
    'consciousness',
]

R1_SYMPTOMS = {
    'unresponsive': 'Unresponsive patient',
    'airway_compromise': 'Airway compromise',
    'active_seizure': 'Active seizure',
    'severe_bleeding': 'Severe bleeding',
    'anaphylaxis': 'Anaphylaxis',
}

R2_SYMPTOMS = {
    'chest_pain': 'Chest pain',
    'stroke_signs': 'Stroke signs',
    'severe_breathlessness': 'Severe breathlessness',
    'vomiting_blood': 'Vomiting blood',
}


def _score_band(value, bands):
    for lower, upper, points in bands:
        if lower <= value <= upper:
            return points
    return None


# NEWS2 SpO2 scales (RCP 2017). Scale 1 is the default for most patients.
# Scale 2 is for patients at risk of hypercapnic respiratory failure, where the
# target saturation is lower (88-92%) and the scoring bands differ.
SPO2_SCALE_1 = [(-999, 91, 3), (92, 93, 2), (94, 95, 1), (96, 999, 0)]
SPO2_SCALE_2 = [(-999, 83, 3), (84, 85, 2), (86, 87, 1), (88, 92, 0), (93, 94, 1), (95, 96, 2), (97, 999, 3)]

# NEWS2 ACVPU consciousness scale. Only 'alert' scores 0; new confusion, voice,
# pain and unresponsive each score 3. The category is kept so the NEWS2-specific
# 'new confusion' signal is not discarded.
ACVPU_POINTS = {'alert': 0, 'confusion': 3, 'voice': 3, 'pain': 3, 'unresponsive': 3}


def _score_spo2(spo2, scale):
    bands = SPO2_SCALE_2 if scale == 2 else SPO2_SCALE_1
    return _score_band(spo2, bands)


def _score_consciousness(consciousness):
    return ACVPU_POINTS.get(consciousness, 3)


def _score_observations(observations, spo2_scale=1):
    missing = []
    warnings = []
    parts = {}

    for field in REQUIRED_OBSERVATIONS:
        if observations.get(field) is None:
            missing.append(field)

    if missing:
        warnings.append(
            'Missing observations are treated as unknown and raise urgency to at least U3.'
        )
        return {'total': None, 'parameters': {}, 'missing': missing}, warnings, True

    rr = observations['respiratory_rate']
    spo2 = observations['spo2']
    oxygen = observations['supplemental_oxygen']
    temp = observations['temperature_c']
    systolic = observations['systolic_bp']
    pulse = observations['pulse']
    consciousness = observations['consciousness']

    # Prototype implementation of the NEWS2 bands (RCP 2017). The rules are
    # unvalidated in this project and must be reviewed before real use.
    definitions = {
        'respiratory_rate': _score_band(rr, [(-999, 8, 3), (9, 11, 1), (12, 20, 0), (21, 24, 2), (25, 999, 3)]),
        'spo2': _score_spo2(spo2, spo2_scale),
        'supplemental_oxygen': 2 if oxygen else 0,
        'temperature_c': _score_band(temp, [(-999, 35.0, 3), (35.1, 36.0, 1), (36.1, 38.0, 0), (38.1, 39.0, 1), (39.1, 999, 2)]),
        'systolic_bp': _score_band(systolic, [(-999, 90, 3), (91, 100, 2), (101, 110, 1), (111, 219, 0), (220, 999, 3)]),
        'pulse': _score_band(pulse, [(-999, 40, 3), (41, 50, 1), (51, 90, 0), (91, 110, 1), (111, 130, 2), (131, 999, 3)]),
        'consciousness': _score_consciousness(consciousness),
    }

    total = sum(definitions.values())
    for field, points in definitions.items():
        parts[field] = {'value': observations[field], 'points': points}
    parts['spo2']['scale'] = spo2_scale
    parts['consciousness']['acvpu'] = consciousness

    return {'total': total, 'parameters': parts, 'missing': [], 'spo2_scale': spo2_scale}, warnings, False


def _add_rule(fired_rules, rule_id, reason):
    fired_rules.append({'id': rule_id, 'reason': reason})


def _more_urgent(a, b):
    return a if LEVEL_RANK[a] <= LEVEL_RANK[b] else b


def _raise_one_level(level):
    if level == 'U4':
        return 'U3'
    if level == 'U3':
        return 'U2'
    if level == 'U2':
        return 'U1'
    return 'U1'


def assess(inputs):
    observations = inputs.get('observations') or {}
    symptoms = set(inputs.get('symptoms') or [])
    age = inputs.get('age')
    pregnant = bool(inputs.get('pregnant'))
    nurse_concern = bool(inputs.get('nurse_concern'))
    spo2_scale = inputs.get('spo2_scale', 1)

    fired_rules = []
    recommendation = 'U4'
    direct_clinician_assessment = False

    breakdown, warnings, missing_or_unknown = _score_observations(observations, spo2_scale)

    r1_hits = [label for key, label in R1_SYMPTOMS.items() if key in symptoms]
    if r1_hits:
        _add_rule(fired_rules, 'R1', 'Immediate red flag present: ' + ', '.join(r1_hits) + '.')
        recommendation = _more_urgent(recommendation, 'U1')

    r2_hits = [label for key, label in R2_SYMPTOMS.items() if key in symptoms]
    if r2_hits:
        _add_rule(fired_rules, 'R2', 'High-risk symptom present: ' + ', '.join(r2_hits) + '.')
        recommendation = _more_urgent(recommendation, 'U2')

    if breakdown['total'] is not None:
        total = breakdown['total']
        if total >= 7:
            _add_rule(fired_rules, 'R3', f'NEWS2 total is {total}, meeting the U1 threshold of 7 or more.')
            recommendation = _more_urgent(recommendation, 'U1')
        elif total >= 5:
            _add_rule(fired_rules, 'R4', f'NEWS2 total is {total}, meeting the U2 threshold of 5 to 6.')
            recommendation = _more_urgent(recommendation, 'U2')

        max_score = max(parameter['points'] for parameter in breakdown['parameters'].values())
        if max_score == 3:
            _add_rule(fired_rules, 'R5', 'At least one NEWS2 parameter scores 3.')
            recommendation = _more_urgent(recommendation, 'U3')

    if missing_or_unknown:
        _add_rule(fired_rules, 'R6', 'One or more required observations are missing or unknown.')
        recommendation = _more_urgent(recommendation, 'U3')

    if (age is not None and age < 16) or pregnant:
        _add_rule(fired_rules, 'R7', 'Age under 16 or pregnancy requires direct clinician assessment.')
        direct_clinician_assessment = True
        recommendation = _more_urgent(recommendation, 'U3')

    if nurse_concern:
        before = recommendation
        recommendation = _raise_one_level(recommendation)
        _add_rule(fired_rules, 'R9', f'Nurse concern escalates urgency from {before} to {recommendation}.')

    if not fired_rules:
        _add_rule(fired_rules, 'R8', 'Complete data and no configured high-risk rule fired.')
        recommendation = 'U4'

    return {
        'recommendation': recommendation,
        'fired_rules': fired_rules,
        'news2_breakdown': breakdown,
        'warnings': warnings,
        'direct_clinician_assessment': direct_clinician_assessment,
        'rule_version': RULE_VERSION,
    }
