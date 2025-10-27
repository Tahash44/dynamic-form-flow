from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import StepSubmission


@receiver(post_save, sender=StepSubmission)
def on_step_submission_created(sender, instance, created, **kwargs):
    if not created:
        return
    instance.instance.advance_after_submission(instance.step)
    instance.instance.mark_completed_if_done()


@receiver(post_delete, sender=StepSubmission)
def on_step_submission_deleted(sender, instance, **kwargs):
    inst = instance.instance
    proc = inst.process

    if inst.status == 'completed' and not proc.all_steps_completed_for(inst):
        inst.status = 'running'
        inst.completed_at = None
        inst.save(update_fields=['status', 'completed_at'])
