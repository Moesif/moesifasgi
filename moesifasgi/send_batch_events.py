from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SendEventAsync:

    def __init__(self):
        pass

    @classmethod
    def exit_handler(cls, scheduler, debug):
        try:
            # Shut down the scheduler
            scheduler.remove_job('moesif_events_batch_job')
            scheduler.shutdown()
        except Exception as ex:
            if debug:
                logger.info(f"Error while closing the queue or scheduler shut down: {str(ex)}")

    @classmethod
    def send_events(cls, api_client, batch_events, debug):
        try:
            if debug:
                logger.info("Sending events to Moesif")
            batch_events_api_response = api_client.create_events_batch(batch_events)
            if debug:
                logger.info("Events sent successfully")
            # Fetch Config ETag from response header
            batch_events_response_config_etag = batch_events_api_response.get("X-Moesif-Config-ETag")
            # Return Config Etag
            return batch_events_response_config_etag
        except Exception as ex:
            if debug:
                logger.info(f"Error sending event to Moesif: {str(ex)}")
            return None

    def batch_events(self, api_client, moesif_events_queue, debug, batch_size):
        batch_events = []
        try:
            while not moesif_events_queue.empty():
                batch_events.append(moesif_events_queue.get_nowait())
                if len(batch_events) == batch_size:
                    break

            if batch_events:
                batch_response = self.send_events(api_client, batch_events, debug)
                batch_events[:] = []
                return batch_response, datetime.utcnow()
            else:
                if debug:
                    logger.info("No events to send")
                # Set the last time event job ran but no message to read from the queue
                return None, datetime.utcnow()
        except:
            if debug:
                logger.info("No message to read from the queue")
            # Set the last time event job ran when exception occurred while sending event
            return None, datetime.utcnow()
