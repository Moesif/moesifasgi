from datetime import datetime
from moesifapi.exceptions.api_exception import *
import json
import logging

logger = logging.getLogger(__name__)

# Application Configuration
class AppConfig:

    def __init__(self):
        pass

    @classmethod
    def get_config(cls, api_client, debug):
        """Get Config"""
        try:
            config_api_response = api_client.get_app_config()
            return config_api_response
        except APIException as inst:
            if 401 <= inst.response_code <= 403:
                logger.error("Unauthorized access getting application configuration. Please check your Application Id.")
            if debug:
                logger.info(f"Error getting application configuration, with status code: {inst.response_code}")
        except Exception as ex:
            if debug:
                logger.info(f"Error getting application configuration: {str(ex)}")

    @classmethod
    def parse_configuration(cls, config, debug):
        """Parse configuration object and return Etag, sample rate and last updated time"""
        try:
            return config.headers.get("X-Moesif-Config-ETag"), json.loads(config.raw_body).get('sample_rate', 100), datetime.utcnow()
        except:
            if debug:
                logger.info('Error while parsing the configuration object, setting the sample rate to default')
            return None, 100, datetime.utcnow()

    @classmethod
    def get_sampling_percentage(cls, config, user_id, company_id):
        """Get sampling percentage"""

        if config is not None:
            try:
                config_body = json.loads(config.raw_body)

                user_sample_rate = config_body.get('user_sample_rate', None)

                company_sample_rate = config_body.get('company_sample_rate', None)

                if user_id and user_sample_rate and user_id in user_sample_rate:
                    return user_sample_rate[user_id]

                if company_id and company_sample_rate and company_id in company_sample_rate:
                    return company_sample_rate[company_id]

                return config_body.get('sample_rate', 100)
            except Exception as e:
                logger.warning(f"Error while parsing user or company sample rate:{str(e)}")

        # Use default
        return 100
