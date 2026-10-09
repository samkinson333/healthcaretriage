import json

from django.test import TestCase
from django.urls import reverse

from .models import Patient, VitalMeasurement


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
