import json

from django.test import TestCase
from django.urls import reverse

from datetime import datetime, timedelta, timezone

from .assessment import assess
from .models import Patient, QueueEvent, TriageAssessment, VitalMeasurement
from .queue import advance_demo_clock, get_waiting_queue
from .validation import validate_assessment


class PatientApiTests(TestCase):
    def test_register_patient_generates_reference(self):
        response = self.client.post(
            reverse('patients-collection'),
            data=json.dumps({'full_name': 'Jane Roe', 'age': 30, 'sex': 'female'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['reference'], 'PAT-0001')

    def test_register_patient_rejects_implausible_age(self):
        response = self.client.post(
            reverse('patients-collection'),
            data=json.dumps({'age': 999}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('age', response.json()['errors'])

    def test_list_patients(self):
        Patient.objects.create(full_name='A', age=20)
        response = self.client.get(reverse('patients-collection'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['patients']), 1)


class VitalApiTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(full_name='Test Patient', age=45, sex='male')
        self.url = reverse('patient-vitals', args=[self.patient.id])

    def _post(self, payload):
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
        )

    def valid_payload(self, **overrides):
        payload = {
            'systolic_bp': 120,
            'diastolic_bp': 80,
            'pulse': 72,
            'temperature_c': 36.8,
            'spo2': 98,
        }
        payload.update(overrides)
        return payload

    def test_submit_vitals_links_to_patient(self):
        response = self._post(self.valid_payload())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['patient_id'], self.patient.id)
        self.assertEqual(VitalMeasurement.objects.count(), 1)

    def test_retrieve_vitals(self):
        self._post(self.valid_payload())
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['measurements']), 1)
        self.assertEqual(response.json()['patient']['reference'], self.patient.reference)

    def test_missing_vital_is_rejected(self):
        payload = self.valid_payload()
        del payload['temperature_c']
        response = self._post(payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('temperature_c', response.json()['errors'])

    def test_implausible_spo2_is_rejected(self):
        response = self._post(self.valid_payload(spo2=140))
        self.assertEqual(response.status_code, 400)
        self.assertIn('spo2', response.json()['errors'])

    def test_systolic_must_exceed_diastolic(self):
        response = self._post(self.valid_payload(systolic_bp=80, diastolic_bp=120))
        self.assertEqual(response.status_code, 400)
        self.assertIn('systolic_bp', response.json()['errors'])

    def test_non_numeric_value_is_rejected(self):
        response = self._post(self.valid_payload(pulse='fast'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('pulse', response.json()['errors'])

    def test_vitals_for_unknown_patient_returns_404(self):
        response = self.client.post(
            reverse('patient-vitals', args=[9999]),
            data=json.dumps(self.valid_payload()),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)

    def test_invalid_json_body_is_rejected(self):
        response = self.client.post(self.url, data='not json', content_type='application/json')
        self.assertEqual(response.status_code, 400)


class AssessmentEngineTests(TestCase):
    def valid_input(self, **overrides):
        data = {
            'age': 40,
            'pregnant': False,
            'observations': {
                'respiratory_rate': 16,
                'spo2': 98,
                'supplemental_oxygen': False,
                'temperature_c': 36.8,
                'systolic_bp': 120,
                'pulse': 72,
                'consciousness': 'alert',
            },
            'symptoms': [],
            'nurse_concern': False,
        }
        data.update(overrides)
        return data

    def test_complete_low_risk_input_returns_u4_r8_and_news2_zero(self):
        result = assess(self.valid_input())
        self.assertEqual(result['recommendation'], 'U4')
        self.assertEqual(result['news2_breakdown']['total'], 0)
        self.assertEqual([rule['id'] for rule in result['fired_rules']], ['R8'])

    def test_immediate_red_flag_returns_u1(self):
        result = assess(self.valid_input(symptoms=['unresponsive']))
        self.assertEqual(result['recommendation'], 'U1')
        self.assertIn('R1', [rule['id'] for rule in result['fired_rules']])

    def test_high_risk_symptom_returns_at_least_u2(self):
        result = assess(self.valid_input(symptoms=['chest_pain']))
        self.assertEqual(result['recommendation'], 'U2')
        self.assertIn('R2', [rule['id'] for rule in result['fired_rules']])

    def test_news2_total_seven_or_more_returns_u1(self):
        result = assess(self.valid_input(observations={
            'respiratory_rate': 25,
            'spo2': 91,
            'supplemental_oxygen': True,
            'temperature_c': 36.8,
            'systolic_bp': 120,
            'pulse': 72,
            'consciousness': 'alert',
        }))
        self.assertEqual(result['recommendation'], 'U1')
        self.assertEqual(result['news2_breakdown']['total'], 8)
        self.assertIn('R3', [rule['id'] for rule in result['fired_rules']])

    def test_news2_total_five_to_six_returns_u2(self):
        result = assess(self.valid_input(observations={
            'respiratory_rate': 21,
            'spo2': 93,
            'supplemental_oxygen': False,
            'temperature_c': 36.8,
            'systolic_bp': 120,
            'pulse': 91,
            'consciousness': 'alert',
        }))
        self.assertEqual(result['recommendation'], 'U2')
        self.assertEqual(result['news2_breakdown']['total'], 5)
        self.assertIn('R4', [rule['id'] for rule in result['fired_rules']])

    def test_spo2_scale_2_scores_target_range_as_zero(self):
        result = assess(self.valid_input(
            spo2_scale=2,
            observations={
                'respiratory_rate': 16,
                'spo2': 90,
                'supplemental_oxygen': False,
                'temperature_c': 36.8,
                'systolic_bp': 120,
                'pulse': 72,
                'consciousness': 'alert',
            },
        ))
        self.assertEqual(result['news2_breakdown']['total'], 0)
        self.assertEqual(result['news2_breakdown']['spo2_scale'], 2)
        self.assertEqual(result['news2_breakdown']['parameters']['spo2']['points'], 0)
        self.assertEqual(result['recommendation'], 'U4')

    def test_spo2_scale_2_boundaries_match_news2_bands(self):
        expected_points = {
            83: 3,
            84: 2,
            85: 2,
            86: 1,
            87: 1,
            88: 0,
            92: 0,
            93: 1,
            94: 1,
            95: 2,
            96: 2,
            97: 3,
        }
        for spo2, expected in expected_points.items():
            with self.subTest(spo2=spo2):
                observations = self.valid_input()['observations']
                observations['spo2'] = spo2
                result = assess(self.valid_input(spo2_scale=2, observations=observations))
                self.assertEqual(result['news2_breakdown']['parameters']['spo2']['points'], expected)

    def test_consciousness_keeps_acvpu_category_and_scores_three_when_not_alert(self):
        for category in ('confusion', 'voice', 'pain', 'unresponsive'):
            with self.subTest(category=category):
                observations = self.valid_input()['observations']
                observations['consciousness'] = category
                result = assess(self.valid_input(observations=observations))
                consciousness = result['news2_breakdown']['parameters']['consciousness']
                self.assertEqual(consciousness['points'], 3)
                self.assertEqual(consciousness['acvpu'], category)

    def test_single_parameter_score_three_returns_at_least_u3(self):
        result = assess(self.valid_input(observations={
            'respiratory_rate': 8,
            'spo2': 98,
            'supplemental_oxygen': False,
            'temperature_c': 36.8,
            'systolic_bp': 120,
            'pulse': 72,
            'consciousness': 'alert',
        }))
        self.assertEqual(result['recommendation'], 'U3')
        self.assertIn('R5', [rule['id'] for rule in result['fired_rules']])

    def test_missing_observation_returns_u3_and_no_misleading_total(self):
        observations = self.valid_input()['observations']
        observations['pulse'] = None
        result = assess(self.valid_input(observations=observations))
        self.assertEqual(result['recommendation'], 'U3')
        self.assertIsNone(result['news2_breakdown']['total'])
        self.assertIn('R6', [rule['id'] for rule in result['fired_rules']])
        self.assertTrue(result['warnings'])

    def test_partial_observations_with_red_flag_are_not_downgraded_by_r6(self):
        observations = self.valid_input()['observations']
        observations['pulse'] = None
        result = assess(self.valid_input(observations=observations, symptoms=['chest_pain']))
        self.assertEqual(result['recommendation'], 'U2')
        self.assertIn('R2', [rule['id'] for rule in result['fired_rules']])
        self.assertIn('R6', [rule['id'] for rule in result['fired_rules']])

    def test_child_or_pregnancy_requires_direct_clinician_assessment(self):
        child = assess(self.valid_input(age=15))
        pregnant = assess(self.valid_input(pregnant=True))
        self.assertEqual(child['recommendation'], 'U3')
        self.assertTrue(child['direct_clinician_assessment'])
        self.assertEqual(pregnant['recommendation'], 'U3')
        self.assertTrue(pregnant['direct_clinician_assessment'])

    def test_nurse_concern_raises_one_level_but_never_to_u5(self):
        result = assess(self.valid_input(nurse_concern=True))
        self.assertEqual(result['recommendation'], 'U3')
        self.assertIn('R9', [rule['id'] for rule in result['fired_rules']])

    def test_automation_never_assigns_u5(self):
        result = assess(self.valid_input())
        self.assertNotEqual(result['recommendation'], 'U5')


class AssessmentValidationTests(TestCase):
    def valid_payload(self, **overrides):
        payload = {
            'age': 42,
            'pregnant': False,
            'observations': {
                'respiratory_rate': {'value': 16, 'source': 'manual'},
                'spo2': {'value': 98, 'source': 'device'},
                'supplemental_oxygen': {'value': False, 'source': 'manual'},
                'temperature_c': {'value': 36.8, 'source': 'manual'},
                'systolic_bp': {'value': 120, 'source': 'manual'},
                'pulse': {'value': 72, 'source': 'device'},
                'consciousness': {'value': 'alert', 'source': 'manual'},
            },
            'symptoms': ['chest_pain'],
            'nurse_concern': False,
        }
        payload.update(overrides)
        return payload

    def test_valid_complete_assessment_payload_is_cleaned(self):
        cleaned, errors = validate_assessment(self.valid_payload())
        self.assertEqual(errors, {})
        self.assertEqual(cleaned['observations']['pulse'], 72)
        self.assertEqual(cleaned['sources']['pulse'], 'device')
        self.assertEqual(cleaned['symptoms'], ['chest_pain'])

    def test_missing_observation_is_allowed_as_none(self):
        payload = self.valid_payload()
        payload['observations']['pulse']['value'] = None
        cleaned, errors = validate_assessment(payload)
        self.assertEqual(errors, {})
        self.assertIsNone(cleaned['observations']['pulse'])

    def test_bool_is_invalid_for_numeric_observation(self):
        payload = self.valid_payload()
        payload['observations']['pulse']['value'] = True
        cleaned, errors = validate_assessment(payload)
        self.assertIn('observations.pulse', errors)

    def test_out_of_range_value_returns_field_error(self):
        payload = self.valid_payload()
        payload['observations']['spo2']['value'] = 140
        cleaned, errors = validate_assessment(payload)
        self.assertIn('observations.spo2', errors)

    def test_malformed_payload_sections_return_errors_not_exceptions(self):
        cleaned, errors = validate_assessment({'age': 'old', 'observations': [], 'symptoms': 'chest'})
        self.assertIn('age', errors)
        self.assertIn('observations', errors)
        self.assertIn('symptoms', errors)

    def test_unknown_symptom_and_source_are_rejected(self):
        payload = self.valid_payload(symptoms=['made_up'])
        payload['observations']['pulse']['source'] = 'watch'
        cleaned, errors = validate_assessment(payload)
        self.assertIn('symptoms', errors)
        self.assertIn('observations.pulse.source', errors)

    def test_spo2_scale_defaults_to_scale_one_and_accepts_scale_two(self):
        cleaned, errors = validate_assessment(self.valid_payload())
        self.assertEqual(errors, {})
        self.assertEqual(cleaned['spo2_scale'], 1)

        cleaned, errors = validate_assessment(self.valid_payload(spo2_scale=2))
        self.assertEqual(errors, {})
        self.assertEqual(cleaned['spo2_scale'], 2)

    def test_invalid_spo2_scale_values_are_rejected(self):
        for scale in (0, 3, True, '2'):
            with self.subTest(scale=scale):
                cleaned, errors = validate_assessment(self.valid_payload(spo2_scale=scale))
                self.assertIn('spo2_scale', errors)

    def test_numeric_strings_are_cleaned_but_empty_string_is_missing(self):
        payload = self.valid_payload()
        payload['observations']['pulse']['value'] = '91'
        payload['observations']['temperature_c']['value'] = ''
        cleaned, errors = validate_assessment(payload)
        self.assertEqual(errors, {})
        self.assertEqual(cleaned['observations']['pulse'], 91)
        self.assertIsNone(cleaned['observations']['temperature_c'])


class QueueSelectorTests(TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
        self.patient_a = Patient.objects.create(full_name='A', age=30)
        self.patient_b = Patient.objects.create(full_name='B', age=30)
        self.patient_c = Patient.objects.create(full_name='C', age=30)

    def make_assessment(self, patient, level, minutes_waiting, state='waiting'):
        return TriageAssessment.objects.create(
            patient=patient,
            inputs={'complaint': f'{level} case'},
            recommendation=level,
            effective_level=level,
            fired_rules=[{'id': 'R8', 'reason': 'Test rule'}],
            news2_breakdown={},
            warnings=[],
            rule_version='prototype-1',
            state=state,
            arrived_at=self.now - timedelta(minutes=minutes_waiting),
        )

    def test_higher_urgency_orders_before_earlier_lower_urgency(self):
        low = self.make_assessment(self.patient_a, 'U4', 30)
        high = self.make_assessment(self.patient_b, 'U2', 5)
        queue = get_waiting_queue(now=self.now)
        self.assertEqual([item['id'] for item in queue], [high.id, low.id])

    def test_same_level_orders_by_arrival_time(self):
        later = self.make_assessment(self.patient_a, 'U3', 10)
        earlier = self.make_assessment(self.patient_b, 'U3', 20)
        queue = get_waiting_queue(now=self.now)
        self.assertEqual([item['id'] for item in queue], [earlier.id, later.id])

    def test_u4_ages_to_u3_at_sixty_minutes_and_not_before(self):
        not_aged = self.make_assessment(self.patient_a, 'U4', 59)
        aged = self.make_assessment(self.patient_b, 'U4', 60)
        queue = {item['id']: item for item in get_waiting_queue(now=self.now)}
        self.assertEqual(queue[not_aged.id]['display_level'], 'U4')
        self.assertIsNone(queue[not_aged.id]['aged_from'])
        self.assertEqual(queue[aged.id]['display_level'], 'U3')
        self.assertEqual(queue[aged.id]['aged_from'], 'U4')

    def test_aged_u4_sorts_below_true_u3(self):
        aged = self.make_assessment(self.patient_a, 'U4', 60)
        true_u3 = self.make_assessment(self.patient_b, 'U3', 5)
        queue = get_waiting_queue(now=self.now)
        self.assertEqual([item['id'] for item in queue], [true_u3.id, aged.id])

    def test_wait_alert_thresholds_and_non_waiting_exclusion(self):
        u2_alert = self.make_assessment(self.patient_a, 'U2', 16)
        self.make_assessment(self.patient_b, 'U1', 10, state='in_consultation')
        queue = get_waiting_queue(now=self.now)
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]['id'], u2_alert.id)
        self.assertTrue(queue[0]['needs_reassessment'])

    def test_advance_demo_clock_accepts_only_demo_increments(self):
        current = advance_demo_clock(15)
        self.assertEqual(current.isoformat(), '2026-10-09T10:15:00+00:00')
        with self.assertRaises(ValueError):
            advance_demo_clock(-15)
        with self.assertRaises(ValueError):
            advance_demo_clock(999)

    def test_api_advance_clock(self):
        response = self.client.post(
            reverse('demo-clock'),
            data=json.dumps({'minutes': 15}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('clock', response.json())

    def test_get_queue(self):
        TriageAssessment.objects.create(
            patient=Patient.objects.create(full_name='QueuePatient', age=50),
            inputs={},
            recommendation='U2',
            effective_level='U2',
            state='waiting',
            arrived_at=datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc),
        )
        response = self.client.get(reverse('queue-list'))
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body['queue']), 1)
        self.assertEqual(body['queue'][0]['effective_level'], 'U2')


class AssessmentApiTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(full_name='Synthetic', age=50, sex='other')
        self.collection_url = reverse('patient-assessments', args=[self.patient.id])

    def valid_payload(self, **overrides):
        payload = {
            'age': 50,
            'pregnant': False,
            'complaint': 'Mild cough',
            'observations': {
                'respiratory_rate': {'value': 16, 'source': 'manual'},
                'spo2': {'value': 98, 'source': 'manual'},
                'supplemental_oxygen': {'value': False, 'source': 'manual'},
                'temperature_c': {'value': 36.8, 'source': 'manual'},
                'systolic_bp': {'value': 120, 'source': 'manual'},
                'pulse': {'value': 72, 'source': 'manual'},
                'consciousness': {'value': 'alert', 'source': 'manual'},
            },
            'symptoms': [],
            'nurse_concern': False,
        }
        payload.update(overrides)
        return payload

    def _post(self, payload):
        return self.client.post(self.collection_url, data=json.dumps(payload), content_type='application/json')

    def test_create_assessment_persists_recommendation_and_reasons(self):
        response = self._post(self.valid_payload(symptoms=['chest_pain']))
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body['recommendation'], 'U2')
        self.assertEqual(body['effective_level'], 'U2')
        self.assertEqual(body['patient']['reference'], self.patient.reference)
        self.assertIn('R2', [rule['id'] for rule in body['fired_rules']])
        assessment = TriageAssessment.objects.get(id=body['id'])
        self.assertEqual(assessment.recommendation, 'U2')
        self.assertEqual(assessment.effective_level, 'U2')

    def test_get_assessment_round_trip_returns_saved_snapshot(self):
        created = self._post(self.valid_payload()).json()
        response = self.client.get(reverse('assessment-detail', args=[created['id']]))
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['id'], created['id'])
        self.assertEqual(body['inputs']['observations']['pulse'], 72)
        self.assertEqual(body['rule_version'], 'prototype-1')

    def test_create_for_unknown_patient_returns_404(self):
        response = self.client.post(
            reverse('patient-assessments', args=[9999]),
            data=json.dumps(self.valid_payload()),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)

    def test_get_unknown_assessment_returns_404(self):
        response = self.client.get(reverse('assessment-detail', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_invalid_assessment_payload_returns_field_errors(self):
        response = self._post({'age': 'old', 'observations': []})
        self.assertEqual(response.status_code, 400)
        self.assertIn('age', response.json()['errors'])
        self.assertIn('observations', response.json()['errors'])

    def test_escalate_deterioration(self):
        created = self._post(self.valid_payload(symptoms=[])).json()
        self.assertEqual(created['effective_level'], 'U4')
        url = reverse('record-deterioration', args=[created['id']])

        # U4 -> U3
        res = self.client.post(url, data=json.dumps({'request_id': 'r1'}), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['effective_level'], 'U3')

        # U3 -> U2
        res = self.client.post(url, data=json.dumps({'request_id': 'r2'}), content_type='application/json')
        self.assertEqual(res.json()['effective_level'], 'U2')

        # U2 -> U1
        res = self.client.post(url, data=json.dumps({'request_id': 'r3'}), content_type='application/json')
        self.assertEqual(res.json()['effective_level'], 'U1')

        # U1 cannot escalate further
        res = self.client.post(url, data=json.dumps({'request_id': 'r4'}), content_type='application/json')
        self.assertEqual(res.status_code, 400)

        # Check events
        events = list(QueueEvent.objects.filter(assessment_id=created['id']).order_by('occurred_at', 'id'))
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0].before['effective_level'], 'U4')
        self.assertEqual(events[0].after['effective_level'], 'U3')

    def test_deterioration_returns_404_for_unknown_assessment(self):
        res = self.client.post(reverse('record-deterioration', args=[9999]))
        self.assertEqual(res.status_code, 404)

    def test_deterioration_not_allowed_for_non_waiting(self):
        created = self._post(self.valid_payload(symptoms=[])).json()
        assessment = TriageAssessment.objects.get(id=created['id'])
        assessment.state = TriageAssessment.State.IN_CONSULTATION
        assessment.save()

        url = reverse('record-deterioration', args=[created['id']])
        res = self.client.post(url)
        self.assertEqual(res.status_code, 400)
        self.assertIn('Only waiting patients', res.json()['error'])

    def test_assign_responder_records_assignment_for_u1_u2_queue_case(self):
        created = self._post(self.valid_payload(symptoms=['chest_pain'])).json()
        url = reverse('assign-responder', args=[created['id']])
        response = self.client.post(
            url,
            data=json.dumps({'role': 'nurse', 'assignee': 'Nurse A'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['assignment'], {'role': 'nurse', 'assignee': 'Nurse A'})

        queue_response = self.client.get(reverse('queue-list'))
        self.assertEqual(queue_response.json()['queue'][0]['assignment'], {'role': 'nurse', 'assignee': 'Nurse A'})

    def test_assign_responder_rejects_non_emergency_case(self):
        created = self._post(self.valid_payload(symptoms=[])).json()
        response = self.client.post(
            reverse('assign-responder', args=[created['id']]),
            data=json.dumps({'role': 'nurse', 'assignee': 'Nurse A'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('assignment', response.json()['errors'])

    def test_assign_responder_validates_payload(self):
        created = self._post(self.valid_payload(symptoms=['chest_pain'])).json()
        response = self.client.post(
            reverse('assign-responder', args=[created['id']]),
            data=json.dumps({'role': 'doctor', 'assignee': ''}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('role', response.json()['errors'])
        self.assertIn('assignee', response.json()['errors'])


class AssessmentModelTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(full_name='Synthetic', age=40, sex='female')
        self.arrived_at = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)

    def test_assessment_links_to_patient_and_defaults_effective_level(self):
        assessment = TriageAssessment.objects.create(
            patient=self.patient,
            inputs={'observations': {'pulse': 72}},
            recommendation='U4',
            effective_level='U4',
            fired_rules=[{'id': 'R8', 'reason': 'No other rule fired.'}],
            news2_breakdown={'total': 0},
            warnings=[],
            rule_version='prototype-1',
            state='waiting',
            arrived_at=self.arrived_at,
        )
        self.assertEqual(assessment.patient, self.patient)
        self.assertEqual(assessment.effective_level, assessment.recommendation)
        self.assertEqual(assessment.state, 'waiting')

    def test_queue_events_are_ordered_newest_first(self):
        assessment = TriageAssessment.objects.create(
            patient=self.patient,
            inputs={},
            recommendation='U4',
            effective_level='U4',
            fired_rules=[],
            news2_breakdown={},
            warnings=[],
            rule_version='prototype-1',
            state='waiting',
            arrived_at=self.arrived_at,
        )
        earlier = QueueEvent.objects.create(
            assessment=assessment,
            event_type='deterioration',
            before={'effective_level': 'U4'},
            after={'effective_level': 'U3'},
            reason='Recorded deterioration',
            occurred_at=datetime(2026, 10, 9, 10, 10, tzinfo=timezone.utc),
        )
        later = QueueEvent.objects.create(
            assessment=assessment,
            event_type='deterioration',
            before={'effective_level': 'U3'},
            after={'effective_level': 'U2'},
            reason='Recorded deterioration',
            occurred_at=datetime(2026, 10, 9, 10, 20, tzinfo=timezone.utc),
        )
        self.assertEqual(list(assessment.events.all()), [later, earlier])
