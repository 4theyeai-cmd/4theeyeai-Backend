from fastapi import APIRouter, HTTPException
from api.schemas.girlfriend_schema import ChatRequest, ChatResponse, Message
from api.services.openai_service import OpenAIService
from api.services.avashow_service import AvashowService
from api.services.lipsync_service import LipSyncService
from api.services.file_service import FileService
from api.services.elevenlabs_service import ElevenLabsService
import os
import logging
import tempfile

# تنظیم لاگر
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


def get_avashow_api_key():
    return os.getenv("AVASHOW_GATEWAY_TOKEN")


def get_temp_audio_dir():
    """Get a writable directory for audio files"""
    # Try different writable directories
    possible_dirs = [
        "/tmp",
        tempfile.gettempdir(),
        os.getcwd(),
        os.path.join(os.getcwd(), "temp"),
    ]

    for dir_path in possible_dirs:
        try:
            # Test if we can write to this directory
            test_file = os.path.join(dir_path, "test_write.tmp")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            logger.info(f"Using writable directory: {dir_path}")
            return dir_path
        except (OSError, IOError) as e:
            logger.warning(f"Cannot write to {dir_path}: {e}")
            continue

    # If no writable directory found, use current directory
    logger.warning("No writable directory found, using current directory")
    return os.getcwd()


@router.get("/")
def root():
    logger.info("Root endpoint called")
    return {"message": "Hello World!"}


@router.get("/test")
def test():
    logger.info("Test endpoint called")
    return {"status": "ok", "message": "Test route is working!"}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    logger.info(f"Chat endpoint called with message: {request.message}")

    openai_service = OpenAIService()
    avashow_service = AvashowService()
    elevenlabs_service = ElevenLabsService()
    lipsync_service = LipSyncService()
    file_service = FileService()
    api_key = get_avashow_api_key()

    if not request.message:
        logger.info("No message provided, returning default messages")
        # پیام پیش‌فرض (مانند Node)
        default_messages = []

        # بررسی وجود فایل‌های پیش‌فرض
        intro_files = [
            ("audios/intro_0.wav", "audios/intro_0.json"),
            ("audios/intro_1.wav", "audios/intro_1.json"),
        ]

        for wav_file, json_file in intro_files:
            try:
                if os.path.exists(wav_file) and os.path.exists(json_file):
                    default_messages.append(
                        Message(
                            text=(
                                "Hey dear... How was your day?"
                                if "intro_0" in wav_file
                                else "I missed you so much... Please don't go for so long!"
                            ),
                            audio=file_service.audio_file_to_base64(wav_file),
                            lipsync=file_service.read_json_transcript(json_file),
                            facialExpression=(
                                "smile" if "intro_0" in wav_file else "sad"
                            ),
                            animation=(
                                "Talking_1" if "intro_0" in wav_file else "Crying"
                            ),
                        )
                    )
                else:
                    logger.warning(
                        f"Default audio files not found: {wav_file} or {json_file}"
                    )
            except Exception as e:
                logger.error(f"Error reading default files: {e}")

        if not default_messages:
            # اگر فایل‌های پیش‌فرض وجود ندارند، پیام ساده برگردان
            default_messages = [
                Message(
                    text="Hey dear... How was your day?",
                    audio=None,
                    lipsync=None,
                    facialExpression="smile",
                    animation="Talking_1",
                ),
                Message(
                    text="I missed you so much... Please don't go for so long!",
                    audio=None,
                    lipsync=None,
                    facialExpression="sad",
                    animation="Crying",
                ),
            ]

        return ChatResponse(messages=default_messages)

    if not api_key or not os.getenv("OPENAI_API_KEY"):
        logger.warning("API keys not set")
        api_messages = []

        # بررسی وجود فایل‌های API warning
        api_files = [
            ("audios/api_0.wav", "audios/api_0.json"),
            ("audios/api_1.wav", "audios/api_1.json"),
        ]

        for wav_file, json_file in api_files:
            try:
                if os.path.exists(wav_file) and os.path.exists(json_file):
                    api_messages.append(
                        Message(
                            text=(
                                "Please my dear, don't forget to add your API keys!"
                                if "api_0" in wav_file
                                else "You don't want to ruin Wawa Sensei with a crazy ChatGPT and ElevenLabs bill, right?"
                            ),
                            audio=file_service.audio_file_to_base64(wav_file),
                            lipsync=file_service.read_json_transcript(json_file),
                            facialExpression=(
                                "angry" if "api_0" in wav_file else "smile"
                            ),
                            animation="Angry" if "api_0" in wav_file else "Laughing",
                        )
                    )
                else:
                    logger.warning(
                        f"API warning audio files not found: {wav_file} or {json_file}"
                    )
            except Exception as e:
                logger.error(f"Error reading API warning files: {e}")

        if not api_messages:
            # اگر فایل‌های API warning وجود ندارند، پیام ساده برگردان
            api_messages = [
                Message(
                    text="Please my dear, don't forget to add your API keys!",
                    audio=None,
                    lipsync=None,
                    facialExpression="angry",
                    animation="Angry",
                ),
                Message(
                    text="You don't want to ruin Wawa Sensei with a crazy ChatGPT and ElevenLabs bill, right?",
                    audio=None,
                    lipsync=None,
                    facialExpression="smile",
                    animation="Laughing",
                ),
            ]

        return ChatResponse(messages=api_messages)

    try:
        # گرفتن پیام‌ها از OpenAI
        logger.info("Getting response from OpenAI")
        openai_messages: list = openai_service.get_girlfriend_response(request.message)
        logger.info(f"OpenAI returned {len(openai_messages)} messages")

        result_messages = []

        # ایجاد پوشه audios اگر وجود ندارد
        os.makedirs("audios", exist_ok=True)
        logger.info("Using audios directory for file storage")

        for i, message in enumerate(openai_messages):
            logger.info(f"Processing message {i}: {message.get('text', 'No text')}")

            try:
                file_name = os.path.join("audios", f"message_{i}.mp3")
                text_input = message.get("text", "")

                # تبدیل متن به گفتار
                logger.info(f"Converting text to speech: {text_input[:50]}...")
                avashow_service.text_to_speech(text_input, file_name)
                logger.info(f"Audio file created: {file_name}")

                wav_file = os.path.join("audios", f"message_{i}.wav")
                json_file = os.path.join("audios", f"message_{i}.json")

                # تبدیل mp3 به wav
                logger.info(f"Converting {file_name} to {wav_file}")
                lipsync_service.mp3_to_wav(file_name, wav_file)

                # تولید lipsync
                logger.info(f"Generating lipsync for {wav_file}")
                lipsync_service.wav_to_lipsync_json(wav_file, json_file)

                # خواندن فایل‌ها
                audio_base64 = file_service.audio_file_to_base64(file_name)
                lipsync_data = file_service.read_json_transcript(json_file)

                result_messages.append(
                    Message(
                        text=message.get("text", ""),
                        audio=audio_base64,
                        lipsync=lipsync_data,
                        facialExpression=message.get("facialExpression", "default"),
                        animation=message.get("animation", "Idle"),
                    )
                )
                logger.info(f"Message {i} processed successfully with audio")

            except Exception as e:
                logger.error(f"Error processing message {i} with audio: {e}")
                # در صورت خطا، پیام بدون audio و lipsync برگردان
                result_messages.append(
                    Message(
                        text=message.get("text", ""),
                        audio=None,
                        lipsync=None,
                        facialExpression=message.get("facialExpression", "default"),
                        animation=message.get("animation", "Idle"),
                    )
                )

        logger.info(f"Chat completed successfully with {len(result_messages)} messages")
        return ChatResponse(messages=result_messages)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/health")
def health():
    logger.info("Health endpoint called")
    return {"status": "ok", "message": "Backend is running!"}
