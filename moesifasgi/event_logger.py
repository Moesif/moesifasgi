import logging
import json
from moesifapi.moesif_api_client import *
from moesifapi.workers import BatchedWorkerPool
from moesifapi.parse_body import ParseBody

logger = logging.getLogger(__name__)

class EventLogger:

    def __init__(self, settings, config, api_client, debug=False):
        self.dropped_events = 0
        self.DEBUG = debug
        self.worker_pool = BatchedWorkerPool(
            worker_count=settings.get("EVENT_WORKER_COUNT", 2),
            api_client=api_client,
            config=config,
            debug=debug,
            max_queue_size=settings.get("EVENT_QUEUE_SIZE", 1000000),
            batch_size=settings.get("BATCH_SIZE", 100),
            timeout=settings.get("EVENT_BATCH_TIMEOUT", 1),
        )

    def log_event(self, event_data):
        try:
            # Add Event to the queue if able and count the dropped event if at capacity
            if self.worker_pool.add_event(event_data):
                logger.debug("Add Event to the queue")
                if self.DEBUG:
                    logger.info(f"Event added to the queue: {APIHelper.json_serialize(event_data)}")
            else:
                self.dropped_events += 1
                logger.info(f"Dropped Event due to queue capacity drop_count: {str(self.dropped_events)}")
                if self.DEBUG:
                    logger.info(f"Event dropped: {APIHelper.json_serialize(event_data)}")
        # add_event does not throw exceptions so this is unexepected
        except Exception as ex:
            logger.exception(f"Error while adding event to the queue: {str(ex)}")