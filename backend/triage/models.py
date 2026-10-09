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
