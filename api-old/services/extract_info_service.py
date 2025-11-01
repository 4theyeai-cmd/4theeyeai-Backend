import os
import requests
import logging
from api.schemas.extract_info_schema import ExtractInfoRequest

logger = logging.getLogger(__name__)


class ExtractInfoService:
    def __init__(self):
        self.url = os.getenv("EXTERNAL_EXTRACTINFO_SERVICE_URL")
        proxy_url = os.getenv("PROXY_URL")
        self.proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        if self.proxies:
            logger.info("Proxy configured for ExtractInfoService")
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

            response = requests.post(
                self.url, json=payload, timeout=30, proxies=self.proxies
            )
            logger.info(
                f"ExtractInfoService call done status={response.status_code} elapsed={getattr(response, 'elapsed', None)}"
            )
            response.raise_for_status()
            result = response.json()

            logger.info(
                f"External extractInfo service response keys={list(result.keys()) if isinstance(result, dict) else type(result)}"
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
