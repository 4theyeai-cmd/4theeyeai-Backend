import os
import requests
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from api.schemas.extract_info_schema import ExtractInfoRequest

logger = logging.getLogger(__name__)


class ExtractInfoService:
    def __init__(self):
        self.url = os.getenv("EXTERNAL_EXTRACTINFO_SERVICE_URL")
        self.session = requests.Session()
        retries = Retry(
            total=3, backoff_factor=2.0, status_forcelist=[429, 500, 502, 503, 504]
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.headers.update(
            {
                "accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "curl/8.9.1",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            }
        )
        # Set proxies from env vars
        http_proxy = os.getenv("HTTP_PROXY")
        https_proxy = os.getenv("HTTPS_PROXY")
        if http_proxy or https_proxy:
            proxies = {}
            if http_proxy:
                proxies["http://"] = http_proxy
            if https_proxy:
                proxies["https://"] = https_proxy
            self.session.proxies.update(proxies)
            logger.info(f"Proxies set: {proxies}")

        if not self.url:
            raise ValueError(
                "EXTERNAL_EXTRACTINFO_SERVICE_URL environment variable is not set"
            )

    def get_extractInfo_response(self, messages: ExtractInfoRequest):
        # Convert messages to the format expected by external service
        payload = {
            "messages": [
                {"id": msg.id, "text": msg.text, "sender": msg.sender}
                for msg in messages.messages
            ]
        }

        try:
            logger.info(f"Calling external extractInfo service: {self.url}")
            logger.info(f"Payload: {payload}")

            response = self.session.post(
                self.url, json=payload, timeout=30, verify=False
            )
            response.raise_for_status()
            result = response.json()

            logger.info(
                f"External extractInfo service response status={response.status_code} (no proxy)"
            )

            # Validate and return the result
            # The external service should return the same format as before
            expected_fields = [
                "airportName",
                "travelType",
                "travelDate",
                "passengerCount",
                "additionalInfo",
                "flightNumber",
                "passengers",
            ]

            # Check if all required fields are present
            for field in expected_fields:
                if field not in result:
                    logger.warning(
                        f"Missing field '{field}' in external service response"
                    )
                    if field == "passengers":
                        result[field] = []
                    else:
                        result[field] = ""
            # Normalize passengers: map baggageCount -> luggageCount (int)
            normalized_passengers = []
            for p in result.get("passengers", []) or []:
                try:
                    # read possible sources
                    luggage = p.get("luggageCount")
                    if luggage is None:
                        baggage_raw = p.get("baggageCount")
                        if baggage_raw is not None:
                            # try to convert to int; fallback to 0
                            try:
                                luggage = int(str(baggage_raw).strip())
                            except Exception:
                                luggage = 0
                    # build normalized passenger
                    normalized_passengers.append(
                        {
                            "name": p.get("name", ""),
                            "lastName": p.get("lastName", ""),
                            "nationalId": p.get("nationalId", ""),
                            "passportNumber": p.get("passportNumber", ""),
                            "luggageCount": int(luggage) if luggage is not None else 0,
                            "passengerType": p.get("passengerType", ""),
                            "gender": p.get("gender", ""),
                            "nationality": p.get(
                                "nationality", "ایرانی"
                            ),  # ایرانی، غیر ایرانی، دیپلمات
                        }
                    )
                except Exception as norm_err:
                    logger.warning(
                        f"Could not normalize passenger record {p}: {norm_err}"
                    )
            result["passengers"] = normalized_passengers

            # result["flightNumber"] = messages.flightNumber  # type: ignore
            print("get_extractInfo_response", result)

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling external extractInfo service: {e}")
            raise ValueError(f"External service error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in extractInfo service: {e}")
            raise ValueError(f"Service error: {str(e)}")


# Create a global instance for backward compatibility
extract_info_service = ExtractInfoService()


async def call_openai(messages: ExtractInfoRequest):
    """
    Backward compatibility function that uses the external service
    """
    return extract_info_service.get_extractInfo_response(messages)
