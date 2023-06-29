import json
import logging

from SocAI.utils.redactron import replace_with_fake_elements


def summarize(alert_info, sensitive_info, vector_count):
    try:
        cleaned_alert_info, replacements = replace_with_fake_elements(alert_info, sensitive_info)
        cleaned_log_info = cleaned_alert_info['data']

        threat_intel_info = cleaned_alert_info.get('ti_result')
        if threat_intel_info:
            threat_intel_info_text = f"The obtained results from querying the threat intelligence platform for IP " \
                                     f"addresses, domains, and email information are presented in" \
                                     f" JSON format as follows: {json.dumps(threat_intel_info)}"
        else:
            threat_intel_info_text = ""

        payload = f"""{threat_intel_info_text}
        There were {vector_count} similar records in the past.
        Log or Alert Information:
        {cleaned_log_info}
        """

        return payload, replacements

    except KeyError as e:
        logging.error(f"Failed summarizing alert information. Missing key: {e}")
    except Exception as e:
        logging.error(f"Unexpected error occurred while summarizing alert information: {str(e)}")
