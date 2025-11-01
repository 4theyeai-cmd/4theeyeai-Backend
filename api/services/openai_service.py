import os
import requests
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import socket
from hashlib import md5  # برای hash message + session

logger = logging.getLogger(__name__)

# Cache dict for duplicate prevention (session-based)
_cache = {}  # key: session_id + message_hash, value: normalized response


class OpenAIService:
    def __init__(self):
        self.url = os.getenv("EXTERNAL_CHAT_SERVICE_URL")
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

    def get_assistant_response(
        self, user_message: str, session_id: str, language: str = "fa"
    ):
        # Cache check for duplicate
        cache_key = md5(f"{session_id}_{user_message}".encode()).hexdigest()
        if cache_key in _cache:
            logger.info(f"Cache hit for key {cache_key} - returning cached response")
            return _cache[cache_key]

        logger.info("=" * 80)
        logger.info("🚀 STARTING OpenAI Service API Call")
        logger.info("=" * 80)

        # Log input parameters
        logger.info(f"📝 Input Parameters:")
        logger.info(f"   - User Message: '{user_message}'")
        logger.info(f"   - Session ID: '{session_id}'")
        logger.info(f"   - Language: '{language}'")
        logger.info(f"   - Service URL: '{self.url}'")
        logger.info(f"   - Cache Key: {cache_key}")

        # Log session configuration
        logger.info(f"🔧 Session Configuration:")
        logger.info(f"   - Headers: {dict(self.session.headers)}")
        logger.info(f"   - Proxies: {self.session.proxies}")

        payload = {
            "message": user_message,
            "session_id": session_id,
            "language": language,
        }

        logger.info(f"📦 Request Payload: {payload}")

        for attempt in range(3):
            logger.info(f"🔄 Attempt {attempt + 1}/3")
            try:
                timeout = 30

                # Log DNS resolution
                try:
                    ip = socket.gethostbyname("elevenlab-test.vercel.app")
                    logger.info(f"🌐 DNS Resolution: elevenlab-test.vercel.app -> {ip}")
                except Exception as dns_error:
                    logger.error(f"❌ DNS Resolution failed: {dns_error}")

                logger.info(f"📡 Making HTTP POST request to: {self.url}")
                logger.info(f"⏱️  Timeout: {timeout} seconds")

                # Log request details
                logger.info(f"📋 Request Details:")
                logger.info(f"   - Method: POST")
                logger.info(f"   - URL: {self.url}")
                logger.info(f"   - Payload Size: {len(str(payload))} characters")
                logger.info(f"   - Verify SSL: False")

                response = self.session.post(
                    self.url, json=payload, timeout=timeout, verify=False
                )

                # Log response details
                logger.info(f"📨 Response Received:")
                logger.info(f"   - Status Code: {response.status_code}")
                logger.info(f"   - Response Headers: {dict(response.headers)}")
                logger.info(f"   - Response Size: {len(response.content)} bytes")
                logger.info(
                    f"   - Response Time: {response.elapsed.total_seconds():.2f} seconds"
                )

                response.raise_for_status()
                raw_response = response.text
                logger.info(f"📄 Raw Response Text: {raw_response}")

                # Try to decode JSON, fallback if invalid
                try:
                    result = response.json()
                    logger.info(f"✅ JSON Parsing Successful")
                    logger.info(f"📊 Parsed JSON Structure: {type(result)}")
                    logger.info(f"📊 JSON Content: {result}")
                except requests.exceptions.JSONDecodeError as e:
                    logger.error(f"❌ JSON Parsing Failed:")
                    logger.error(f"   - Error: {e}")
                    logger.error(f"   - Raw Response: {raw_response}")
                    logger.error(
                        f"   - Response Length: {len(raw_response)} characters"
                    )
                    return [
                        {
                            "text": "خطا: پاسخ سرور نامعتبر است.",
                            "facialExpression": "default",
                            "animation": "StandingIdle",
                        }
                    ]

                logger.info(
                    f"✅ External chat service response successful (status={response.status_code})"
                )

                # Normalize to List[Dict]
                payload_messages = result.get("messages")
                logger.info(f"🔍 Processing Messages:")
                logger.info(f"   - Messages Type: {type(payload_messages)}")
                logger.info(f"   - Messages Content: {payload_messages}")

                if isinstance(payload_messages, dict) and "text" in payload_messages:
                    logger.info("📝 Processing single message dict")
                    normalized = [
                        {
                            "text": payload_messages.get("text", ""),
                            "facialExpression": payload_messages.get(
                                "facialExpression", "default"
                            ),
                            "animation": payload_messages.get(
                                "animation", "StandingIdle"
                            ),
                        }
                    ]
                elif isinstance(payload_messages, list):
                    logger.info(
                        f"📝 Processing message list with {len(payload_messages)} items"
                    )
                    normalized = []
                    for i, item in enumerate(payload_messages):
                        logger.info(f"   - Processing item {i}: {type(item)} = {item}")
                        if isinstance(item, dict):
                            normalized.append(
                                {
                                    "text": item.get("text", ""),
                                    "facialExpression": item.get(
                                        "facialExpression", "default"
                                    ),
                                    "animation": item.get("animation", "StandingIdle"),
                                }
                            )
                        else:
                            normalized.append(
                                {
                                    "text": str(item),
                                    "facialExpression": "default",
                                    "animation": "StandingIdle",
                                }
                            )
                else:
                    logger.info("📝 Processing fallback case")
                    normalized = [
                        {
                            "text": str(
                                result.get("messages", {}).get("text", str(result))
                            ),
                            "facialExpression": "default",
                            "animation": "StandingIdle",
                        }
                    ]

                logger.info(f"✅ Normalization Complete:")
                logger.info(f"   - Normalized Messages Count: {len(normalized)}")
                for i, msg in enumerate(normalized):
                    logger.info(f"   - Message {i}: {msg}")

                # Cache the response
                _cache[cache_key] = normalized
                logger.info(f"Cache saved for key {cache_key}")

                logger.info("=" * 80)
                logger.info("🎉 OpenAI Service API Call SUCCESSFUL")
                logger.info("=" * 80)
                return normalized

            except requests.exceptions.Timeout:
                logger.warning(
                    f"⏰ Attempt {attempt + 1} timed out after {timeout} seconds"
                )
                if attempt == 2:  # This is the final attempt
                    logger.error("=" * 80)
                    logger.error("💥 ALL ATTEMPTS FAILED - TIMEOUT")
                    logger.error("=" * 80)
                    # Return special error response that will trigger error audio and lipsync
                    return [
                        {
                            "text": "ERROR_SERVICE_UNAVAILABLE",
                            "facialExpression": "sad",
                            "animation": "Sad",
                            "is_error": True,
                            "language": language,
                        }
                    ]
                else:
                    logger.info(f"🔄 Retrying in next attempt...")

            except requests.exceptions.RequestException as e:
                logger.warning(f"❌ Attempt {attempt + 1} failed:")
                logger.warning(f"   - Error Type: {type(e).__name__}")
                logger.warning(f"   - Error Message: {str(e)}")
                logger.warning(f"   - Error Details: {e}")

                if attempt == 2:
                    logger.error("=" * 80)
                    logger.error("💥 ALL ATTEMPTS FAILED")
                    logger.error("=" * 80)
                    logger.error(f"❌ Final Error: {e}")
                    logger.error(f"❌ Error Type: {type(e).__name__}")
                    # Return special error response that will trigger error audio and lipsync
                    return [
                        {
                            "text": "ERROR_SERVICE_UNAVAILABLE",
                            "facialExpression": "sad",
                            "animation": "Sad",
                            "is_error": True,
                            "language": language,
                        }
                    ]
                else:
                    logger.info(f"🔄 Retrying in next attempt...")
