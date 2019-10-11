import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .constants import PIPELINE_STATUS_INITIALIZING, RELEASE_STATUS_OPEN, STEP_FINAL_STATUSES
from .fields import username_on_model
from .models import SCMPipelineRun, SCMRelease, SCMStepRun

log = logging.getLogger('katka')


@receiver(post_save, sender=SCMStepRun)
def update_pipeline_from_steps(sender, **kwargs):
    """
    Update the pipeline 'steps_completed' and 'steps_total' in case they changed whenever a step is updated/added
    """
    pipeline = kwargs['instance'].scm_pipeline_run
    pipeline_steps = SCMStepRun.objects.filter(scm_pipeline_run=pipeline)

    before_steps_total = pipeline.steps_total
    before_steps_completed = pipeline.steps_completed

    pipeline.steps_total = pipeline_steps.count()
    pipeline.steps_completed = pipeline_steps.filter(status__in=STEP_FINAL_STATUSES).count()

    if pipeline.steps_completed != before_steps_completed or pipeline.steps_total != before_steps_total:
        with username_on_model(SCMPipelineRun, kwargs['instance'].modified_username):
            pipeline.save()


@receiver(post_save, sender=SCMPipelineRun)
def send_pipeline_change_notification(sender, **kwargs):
    pipeline = kwargs['instance']
    if kwargs['created'] is True:
        create_release_if_necessary(pipeline)

    if pipeline.status == PIPELINE_STATUS_INITIALIZING and kwargs['created'] is False:
        # Do not send notifications when the pipeline is initializing. While initializing, steps are created and
        # since this is done with several requests, several notifications would be sent, while the only one you
        # care about is when all the steps are created and the status is changed to 'in progress'.
        # There is one exception though, a notify *should* be sent when the pipeline is first created, because
        # the notification will trigger the creation of the steps.
        return

    session = settings.PIPELINE_CHANGE_NOTIFICATION_SESSION
    session.post(
        settings.PIPELINE_CHANGE_NOTIFICATION_URL, json={'public_identifier': str(pipeline.public_identifier)}
    )


def create_release_if_necessary(pipeline):
    releases = SCMRelease.objects.filter(
        status=RELEASE_STATUS_OPEN, scm_pipeline_runs__application=pipeline.application
    )
    with username_on_model(SCMRelease, pipeline.modified_username):
        if len(releases) == 0:
            release = SCMRelease.objects.create()
        elif len(releases) > 1:
            log.error(f'Multiple open releases found for application {pipeline.application.pk}, picking newest')
            release = releases.order_by('-created').first()
        else:
            release = releases[0]

        release.scm_pipeline_runs.add(pipeline)
        release.save()