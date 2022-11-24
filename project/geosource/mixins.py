from datetime import timedelta

from celery import states
from django.utils.timezone import now
from rest_framework.exceptions import MethodNotAllowed

from project.geosource.tasks import run_model_object_method

from .app_settings import MAX_TASK_RUNTIME


class CeleryCallMethodsMixin:

    DONE_STATUSES = ("SUCCESS", "FAILURE", "NEED_SYNC", None)

    def update_status(self, task):
        self.task_id = task.task_id
        self.task_date = now()
        self.save()

    @property
    def can_sync(self):
        """Property containing a boolean that tell if the state allow to run a sync"""
        status = self.get_status()

        return status.get("state") in self.DONE_STATUSES or (
            status.get("state") not in self.DONE_STATUSES
            and self.task_date is not None
            and self.task_date < now() - timedelta(hours=MAX_TASK_RUNTIME)
        )

    def run_async_method(
        self,
        method,
        success_state=states.SUCCESS,
        force=False,
        countdown=None,
    ):
        """Schedule an async task that will be runned by celery.
        Raises an error if a task is already running or scheduled, can be forced with
        `force` argument.
        """
        if self.can_sync or force:
            task_job = run_model_object_method.apply_async(
                (
                    self._meta.app_label,
                    self.__class__.__name__,
                    self.pk,
                    method,
                    success_state,
                ),
                countdown=countdown,
            )

            self.update_status(task_job)
            return task_job

        raise MethodNotAllowed("One job is still running on this source")

    def run_sync_method(self, method, success_state=states.SUCCESS):
        """Run an object method in a synchrone mode.
        The success state of the task can be defined with the `success_state` argument.
        """
        task_job = run_model_object_method.apply(
            (
                self._meta.app_label,
                self.__class__.__name__,
                self.pk,
                method,
                success_state,
            )
        )
        self.update_status(task_job)
        return task_job
