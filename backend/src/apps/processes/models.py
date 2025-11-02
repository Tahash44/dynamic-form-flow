import secrets

from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from apps.forms.models import Form
from apps.users.models import Profile


class Process(models.Model):
    SEQUENTIAL = 'sequential'
    FREE_FLOW = 'free_flow'
    TYPE_CHOICES = [
        (SEQUENTIAL, 'Sequential'),
        (FREE_FLOW, 'Free flow'),
    ]

    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='processes')
    title = models.CharField(max_length=255, default='')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=SEQUENTIAL)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
    
    @property
    def is_sequential(self) -> bool:
        return self.type == self.SEQUENTIAL

    def get_first_step(self):
        return self.steps.order_by('order').first()

    def get_next_step(self, current_step):
        if not self.is_sequential or current_step is None:
            return None
        return self.steps.filter(order__gt=current_step.order).order_by('order').first()

    def all_steps_completed_for(self, instance) -> bool:
        submitted_step_ids = set(
            instance.submissions.values_list('step_id', flat=True)
        )
        required_step_ids = set(self.steps.values_list('id', flat=True))
        return required_step_ids.issubset(submitted_step_ids)

    def __str__(self):
        return self.title or f'Process : #{self.pk}'


class ProcessStep(models.Model):
    process = models.ForeignKey('Process', on_delete=models.CASCADE, related_name='steps')
    form = models.ForeignKey(Form, on_delete=models.PROTECT, related_name='used_in_steps')
    title = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=1, db_index=True, validators=[MinValueValidator(1)])
    allow_skip = models.BooleanField(default=False)  # ⬅️ جدید

    class Meta:
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(fields=['process', 'order'], name='uniq_step_order_per_process'),
        ]
        indexes = [
            models.Index(fields=['process', 'order'], name='idx_process_order'),
        ]

    def __str__(self):
        t = self.title or self.form.name
        return f'{self.process} · Step {self.order}: {t}'


class ProcessInstance(models.Model):
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('aborted', 'Aborted'),
    ]

    process = models.ForeignKey('Process', on_delete=models.CASCADE, related_name='instances')
    started_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='started_processes')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='running')
    current_step = models.ForeignKey('ProcessStep', on_delete=models.SET_NULL,null=True, blank=True,related_name='current_instances')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    access_token = models.CharField(null=True, blank=True, db_index=True, unique=True)
    access_token_expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Instance #{self.pk} of {self.process}'

    def is_done(self):
        return self.status == 'completed'

    def start(self):
        if self.process.is_sequential and not self.current_step:
            self.current_step = self.process.get_first_step()
            self.save(update_fields=['current_step'])

    def mark_completed_if_done(self):
        if self.process.is_sequential:
            if self.current_step is None:
                self.status = 'completed'
                self.completed_at = timezone.now()
                self.save(update_fields=['status', 'completed_at'])
        else:
            if self.process.all_steps_completed_for(self):
                self.status = 'completed'
                self.completed_at = timezone.now()
                self.save(update_fields=['status', 'completed_at'])

    def advance_after_submission(self, step):
        if not self.process.is_sequential:
            return

        if self.current_step and step.id == self.current_step_id:
            next_step = self.process.get_next_step(step)
            if next_step:
                self.current_step = next_step
                self.save(update_fields=['current_step'])
            else:
                self.current_step = None
                self.save(update_fields=['current_step'])
            self.mark_completed_if_done()

    def issue_guest_token(self, ttl_hours: int = 24, force: bool = False):
        if self.started_by_id and not force:
            return

        if self.access_token and not force:
            return

        self.access_token = secrets.token_urlsafe(48)
        self.access_token_expires_at = timezone.now() + timedelta(hours=ttl_hours)
        self.save(update_fields=['access_token', 'access_token_expires_at'])

    def save(self, *args, **kwargs):
        if self.started_by is None and not self.access_token:
            self.access_token = secrets.token_urlsafe(48)
            self.access_token_expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['process', 'status'], name='idx_procinst_proc_status'),
            models.Index(fields=['access_token'], name='idx_procinst_token'),
        ]
        constraints = [
            models.CheckConstraint(
                name='guest_token_only_for_guest',
                check=Q(started_by__isnull=True) | Q(access_token__isnull=False),
            ),
        ]


class StepSubmission(models.Model):
    instance = models.ForeignKey('ProcessInstance', on_delete=models.CASCADE, related_name='submissions')
    step = models.ForeignKey('ProcessStep', on_delete=models.CASCADE, related_name='submissions')
    form_response = models.ForeignKey('forms.Response', on_delete=models.CASCADE,related_name='step_submissions', null=True, blank=True)
    skipped = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['instance', 'step'], name='uniq_instance_step')
        ]
        ordering = ['submitted_at']

    def __str__(self):
        return f'{self.instance} / {self.step}'
