import os
import requests
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# تنظیم لاگر
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAIService:
    def __init__(self):
        self.url = os.getenv(
            "EXTERNAL_CHAT_SERVICE_URL",
            "https://elevenlab-test.vercel.app/assistant/chat",
        )  # پیش‌فرض برای تست
        self.session = requests.Session()
        retries = Retry(
            total=5,  # 5 تلاش برای اطمینان بیشتر
            backoff_factor=1.0,  # فاصله زمانی بین تلاش‌ها (1، 2، 4، 8، 16 ثانیه)
            status_forcelist=[429, 500, 502, 503, 504],
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.headers.update(
            {
                "accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            }
        )

    def get_assistant_response(
        self, user_message: str, session_id: str, language: str = "fa"
    ):
        payload = {
            "message": user_message,
            "session_id": session_id,
            "language": language,
        }

        for attempt in range(5):  # 5 تلاش
            try:
                timeout = 60  # افزایش timeout به 60 ثانیه
                logger.info(f"Attempt {attempt + 1} to call {self.url}")
                response = self.session.post(
                    self.url,
                    json=payload,
                    timeout=timeout,
                    verify=False,  # برای تست لوکال، در prod true کنین
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Success with status {response.status_code}")
                # normaliz کردن خروجی
                payload_messages = result.get("messages", {})
                if isinstance(payload_messages, dict):
                    normalized = [
                        {
                            "text": payload_messages.get("text", ""),
                            "facialExpression": "default",
                            "animation": "Idle",
                        }
                    ]
                else:
                    normalized = [
                        {
                            "text": str(result),
                            "facialExpression": "default",
                            "animation": "Idle",
                        }
                    ]
                return normalized
            except requests.exceptions.Timeout:
                logger.warning(
                    f"Attempt {attempt + 1} timed out after {timeout} seconds"
                )
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == 4:  # آخرین تلاش
                    logger.error(f"All attempts failed. Last error: {e}")
                    raise


# تست مستقیم
if __name__ == "__main__":
    service = OpenAIService()
    response = service.get_assistant_response("test message", "test_session", "fa")
    print("Response:", response)
