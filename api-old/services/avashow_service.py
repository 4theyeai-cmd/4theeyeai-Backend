import os
import requests
import json
import logging

logger = logging.getLogger(__name__)


class AvashowService:
    def __init__(self):
        self.url = os.getenv(
            "AVASHOW_API_URL"
        )  # "https://partai.gw.isahab.ir/TextToSpeech/v1/longText"
        self.gateway_token = os.getenv(
            "AVASHOW_GATEWAY_TOKEN"
        )  # توکن را در .env قرار دهید

    def text_to_speech(self, text: str, file_name: str, speaker: str = "3"):
        payload = json.dumps(
            {
                "data": text,
                "filePath": "true",
                "base64": "0",
                "checksum": "1",
                "speaker": speaker,
            }
        )
        headers = {
            "Content-Type": "application/json",
            "gateway-token": self.gateway_token or "",
        }
        logger.info(f"Sending text to Avashow: {text[:50]}...")
        response = requests.post(self.url, headers=headers, data=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Avashow response: {result}")

        # استخراج آدرس فایل mp3
        audio_path = result.get("data", {}).get("data", {}).get("filePath")
        if not audio_path:
            logger.error("No audio filePath returned from Avashow")
            raise Exception("No audio filePath returned from Avashow")

        # اگر آدرس با http شروع نمی‌شود، اضافه کن
        if not audio_path.startswith("http"):
            audio_url = "https://" + audio_path
        else:
            audio_url = audio_path

        # دانلود فایل mp3
        audio_response = requests.get(audio_url, timeout=60)
        audio_response.raise_for_status()
        with open(file_name, "wb") as f:
            f.write(audio_response.content)
        logger.info(f"Audio file saved: {file_name}")
