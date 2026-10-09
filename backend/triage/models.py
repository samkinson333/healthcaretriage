from django.db import models


class Patient(models.Model):
    class Sex(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        OTHER = 'other', 'Other'

    reference = models.CharField(max_length=20, unique=True, editable=False)
    full_name = models.CharField(max_length=150, blank=True)
    age = models.PositiveIntegerField()
    sex = models.CharField(max_length=10, choices=Sex.choices, default=Sex.OTHER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.reference:
            self.reference = f'PAT-{self.pk:04d}'
            super().save(update_fields=['reference'])

    def __str__(self):
        return self.reference


class TriageAssessment(models.Model):
    class UrgencyLevel(models.TextChoices):
        U1 = 'U1', 'U1 Immediate'
        U2 = 'U2', 'U2 Urgent'
        U3 = 'U3 Soon'
        U4 = 'U4 Standard'
        U5 = 'U5 Low'

    class State(models.TextChoices):
        WAITING = 'waiting', 'Waiting'
        IN_CONSULTATION = 'in_consultation', 'In consultation'
        COMPLETED = 'completed', 'Completed'

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='assessments',
    )
    inputs = models.JSONField(default=dict)
    recommendation = models.CharField(max_length=20, choices=UrgencyLevel.choices)
    effective_level = models.CharField(max_length=20, choices=UrgencyLevel.choices)
    fired_rules = models.JSONField(default=list)
    news2_breakdown = models.JSONField(default=dict)
    warnings = models.JSONField(default=list)
    rule_version = models.CharField(max_length=40)
    state = models.CharField(max_length=20, choices=State.choices, default=State.WAITING)
    arrived_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-arrived_at', '-id']
        indexes = [
            models.Index(fields=['state', 'effective_level', 'arrived_at']),
            models.Index(fields=['patient', '-created_at']),
        ]

    def __str__(self):
        return f'{self.patient.reference} {self.effective_level}'


class QueueEvent(models.Model):
    class EventType(models.TextChoices):
        ASSESSMENT_CREATED = 'assessment_created', 'Assessment created'
        CLOCK_ADVANCED = 'clock_advanced', 'Clock advanced'
        DETERIORATION = 'deterioration', 'Deterioration'
        OVERRIDE = 'override', 'Override'
        STATE_CHANGED = 'state_changed', 'State changed'

    assessment = models.ForeignKey(
        TriageAssessment,
        on_delete=models.CASCADE,
        related_name='events',
    )
    event_type = models.CharField(max_length=40, choices=EventType.choices)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)
    reason = models.TextField(blank=True)
    occurred_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-occurred_at', '-id']
        indexes = [models.Index(fields=['assessment', '-occurred_at'])]

    def __str__(self):
        return f'{self.assessment_id} {self.event_type}'


class VitalMeasurement(models.Model):
    class Source(models.TextChoices):
        MANUAL = 'manual', 'Manual'
        DEVICE = 'device', 'Device (simulated)'

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='vitals',
    )
    systolic_bp = models.PositiveIntegerField()
    diastolic_bp = models.PositiveIntegerField()
    pulse = models.PositiveIntegerField()
    temperature_c = models.DecimalField(max_digits=4, decimal_places=1)
    spo2 = models.PositiveIntegerField()
    source = models.CharField(
        max_length=10,
        choices=Source.choices,
        default=Source.MANUAL,
    )
    measured_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-measured_at', '-id']

    def __str__(self):
        return f'{self.patient.reference} @ {self.measured_at:%Y-%m-%d %H:%M}'
