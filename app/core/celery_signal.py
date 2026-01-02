






import logging

from celery import Task

logger = logging.getLogger(__name__)


class BaseTaskSignal(Task):
    """
    Generic base class for Celery tasks with signal hooks.
    """

    max_retries = 3
    retry_backoff = True
    retry_backoff_max = 300
    retry_jitter = True

    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"[SUCCESS] Task {self.name} ({task_id}) completed successfully.")
        logger.debug(f"Return value: {retval}, Args: {args}, Kwargs: {kwargs}")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"[FAILURE] Task {self.name} ({task_id}) failed with error: {exc}")
        logger.debug(f"Args: {args}, Kwargs: {kwargs}, Traceback: {einfo}")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Retry handler.

        This is run by the worker when the task is to be retried.

        Arguments:
            exc (Exception): The exception sent to :meth:`retry`.
            task_id (str): Unique id of the retried task.
            args (Tuple): Original arguments for the retried task.
            kwargs (Dict): Original keyword arguments for the retried task.
            einfo (~billiard.einfo.ExceptionInfo): Exception information.

        Returns:
            None: The return value of this handler is ignored.
        """
        logger.error(f"[FAILURE] Task {self.name} ({task_id}) failed with error: {exc}")
        logger.debug(f"Args: {args}, Kwargs: {kwargs}, Traceback: {einfo}")


class GenericTaskSignal(BaseTaskSignal):
    """
    On Completion of task
    """

    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"[SUCCESS] Task {self.name} ({task_id}) completed successfully.")
        logger.debug(f"Return value: {retval}, Args: {args}, Kwargs: {kwargs}")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"[FAILURE] Task {self.name} ({task_id}) failed with error: {exc}")
        logger.debug(f"Args: {args}, Kwargs: {kwargs}, Traceback: {einfo}")


