from fastapi import APIRouter, HTTPException
from api.schemas.assistant_schema import ChatRequest, ChatResponse, Message
from api.services.openai_service import OpenAIService
from api.services.avashow_service import AvashowService
from api.services.lipsync_service import LipSyncService
from api.services.file_service import FileService
from api.services.elevenlabs_service import ElevenLabsService
import os
import logging
import tempfile
import re
import socket

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


def clean_text_from_json(text: str) -> str:
    """Remove JSON artifacts from text that might contain OpenAI response formatting."""
    if not text:
        return text

    # Remove JSON-like structures that might be appended to text
    # Pattern to match JSON arrays or objects at the end of text
    json_pattern = r"\s*\[\s*\{.*\}\s*\]\s*$"

    # Remove the JSON part
    cleaned_text = re.sub(json_pattern, "", text, flags=re.DOTALL)

    # Also remove any remaining JSON-like artifacts
    cleaned_text = re.sub(r"\s*\{[^}]*\}\s*", "", cleaned_text)

    # Clean up extra whitespace
    cleaned_text = cleaned_text.strip()

    logger.info(f"Text cleaned: '{text[:100]}...' -> '{cleaned_text[:100]}...'")

    return cleaned_text


@router.get("/")
def root():
    logger.info("Root endpoint called")
    return {"message": "Hello World!"}


@router.get("/test")
def test():
    logger.info("Test endpoint called")
    return {"status": "ok", "message": "Test route is working!"}


@router.get("/test-clean")
def test_text_cleaning():
    """Test the text cleaning function with sample problematic text."""
    test_text = 'در سالن VIP CIP، امکاناتی مثل لانژ اختصاصی، رستوران سلف‌سرویس، اتاق بازی کودکان و اینترنت پرسرعت داریم. خدمات ویژه‌ای مثل Home Check-in، ویلچر و پذیرش حیوان خانگی هم ارائه می‌دیم. اگه سوال دیگه‌ای داری، بگو تا راهنماییت کنم. [ { "text": "در سالن VIP CIP، امکاناتی مثل لانژ اختصاصی، رستوران سلف‌سرویس، اتاق بازی کودکان و اینترنت پرسرعت داریم.", "facialExpression": "smile", "animation": "Talking_0" }, { "text": "خدمات ویژه‌ای مثل Home Check-in، ویلچر و پذیرش حیوان خانگی هم ارائه می‌دیم.", "facialExpression": "smile", "animation": "Talking_1" }, { "text": "اگه سوال دیگه‌ای داری، بگو تا راهنماییت کنم.", "facialExpression": "smile", "animation": "Talking_2" } ]'

    cleaned_text = clean_text_from_json(test_text)

    return {
        "original_text": test_text,
        "cleaned_text": cleaned_text,
        "original_length": len(test_text),
        "cleaned_length": len(cleaned_text),
        "status": "Text cleaning test completed",
    }


@router.get("/intro", response_model=ChatResponse)
def play_introduction(language: str = "fa"):
    """Prepare audio+lip-sync for introduction in selected language (fa or en)."""
    try:
        file_service = FileService()
        lipsync_service = LipSyncService()

        is_english = (language or "").lower().startswith("en")
        base_name = "introduction_en" if is_english else "introduction"

        # Ensure base files exist
        mp3_file = os.path.join("audios", f"{base_name}.mp3")
        if not os.path.exists(mp3_file):
            raise HTTPException(status_code=404, detail=f"File not found: {mp3_file}")

        wav_file = os.path.join("audios", f"{base_name}.wav")
        json_file = os.path.join("audios", f"{base_name}.json")

        # Convert mp3 -> wav if needed
        if not os.path.exists(wav_file):
            lipsync_service.mp3_to_wav(mp3_file, wav_file)

        # Generate lipsync json
        lipsync_service.wav_to_lipsync_json(wav_file, json_file)

        # Read back audio and json
        audio_base64 = file_service.audio_file_to_base64(mp3_file)
        lipsync_data = file_service.read_json_transcript(json_file)

        text = (
            "Hi! I'm Bina, I'm here to make your trip easier. Where are you traveling today? Where would you like to start?"
            if is_english
            else "سلام! من بینادهستم، اینجا کنارتم که سفرت رو راحت کنم. امروز کجا قراره سفر کنی؟ دوست داری از کجا شروع کنیم؟"
        )

        message = Message(
            text=text,
            audio=audio_base64,
            lipsync=lipsync_data,
            facialExpression="smile",
            animation="Idle",  # "Talking_1",
        )

        return ChatResponse(messages=[message])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /intro endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/test-connectivity")
def test_connectivity():
    try:
        response = requests.get(
            "https://elevenlab-test.vercel.app/assistant/health", timeout=30
        )
        response.raise_for_status()
        return {"status": "success", "response": response.json()}
    except Exception as e:
        logger.error(f"Connectivity test failed: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/test-dns")
def test_dns():
    try:
        ip = socket.gethostbyname("elevenlab-test.vercel.app")
        return {"status": "success", "ip": ip}
    except Exception as e:
        logger.error(f"DNS resolution failed: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/chat-text", response_model=ChatResponse)
def chat_text_only(request: ChatRequest):
    """Fast text-only response without audio processing"""
    logger.info(f"Fast chat endpoint called with message: {request.message}")

    openai_service = OpenAIService()

    try:
        # گرفتن پیام‌ها از OpenAI
        logger.info(f"Getting response from OpenAI with language: {request.language}")
        openai_messages: list = openai_service.get_assistant_response(
            request.message, request.session_id, request.language
        )
        logger.info(f"OpenAI returned {len(openai_messages)} messages")

        result_messages = []

        for i, message in enumerate(openai_messages):
            logger.info(f"Processing message {i}: {message.get('text', 'No text')}")

            # فقط متن بدون audio و lipsync
            result_messages.append(
                Message(
                    text=clean_text_from_json(message.get("text", "")),
                    audio=None,
                    lipsync=None,
                    facialExpression=message.get("facialExpression", "default"),
                    animation=message.get("animation", "Idle"),
                )
            )

        logger.info(
            f"Fast chat completed successfully with {len(result_messages)} messages"
        )
        return ChatResponse(messages=result_messages)

    except Exception as e:
        logger.error(f"Error in fast chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    logger.info(f"Chat endpoint called with message: {request.message}")

    # Check if audio should be disabled for faster response
    disable_audio = (
        os.getenv("DISABLE_AUDIO_GENERATION", "false").lower() == "true"
    )  # Default to true for faster response
    logger.info(
        f"DISABLE_AUDIO_GENERATION environment variable: {os.getenv('DISABLE_AUDIO_GENERATION', 'not set')}"
    )
    logger.info(f"Audio generation disabled: {disable_audio}")
    if disable_audio:
        logger.info("Audio generation is disabled for faster response")

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

    # Validate required API keys depending on language
    is_english = (request.language or "").lower().startswith("en")
    if (not os.getenv("OPENAI_API_KEY")) or (not is_english and not api_key):
        logger.warning("API keys missing for the requested operation")
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
        logger.info(f"Getting response from OpenAI with language: {request.language}")
        openai_messages: list = openai_service.get_assistant_response(
            request.message, request.session_id, request.language
        )
        logger.info(f"OpenAI returned {len(openai_messages)} messages")

        result_messages = []

        # استفاده از مسیر قابل نوشتن
        audio_dir = get_temp_audio_dir()
        logger.info(f"Using audio directory: {audio_dir}")

        # بررسی قابلیت نوشتن در مسیر
        can_write_files = True
        logger.info(f"Checking write permissions for audio directory: {audio_dir}")
        try:
            test_file = os.path.join(audio_dir, "test_write.tmp")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            logger.info(f"Write test successful for directory: {audio_dir}")
        except Exception as e:
            logger.warning(f"Cannot write files to {audio_dir}: {e}")
            can_write_files = False
            logger.info(f"can_write_files set to: {can_write_files}")

        for i, message in enumerate(openai_messages):
            logger.info(f"Processing message {i}: {message.get('text', 'No text')}")

            if can_write_files and not disable_audio:
                logger.info(
                    f"Processing message {i} with audio generation - can_write_files: {can_write_files}, disable_audio: {disable_audio}"
                )
                try:
                    # Ensure audios directory exists
                    audios_dir = "audios"
                    logger.info(f"Creating audios directory: {audios_dir}")
                    os.makedirs(audios_dir, exist_ok=True)
                    logger.info(
                        f"Audios directory exists: {os.path.exists(audios_dir)}"
                    )

                    file_name = os.path.join(audios_dir, f"message_{i}.mp3")
                    text_input = message["text"]
                    logger.info(f"Target audio file: {file_name}")
                    logger.info(f"Text to convert: {text_input[:100]}...")

                    # تبدیل متن به گفتار - انتخاب سرویس بر اساس زبان
                    logger.info(f"Converting text to speech: {text_input[:50]}...")
                    try:
                        if is_english:
                            logger.info("Using ElevenLabsService for English TTS")
                            elevenlabs_service.text_to_speech(text_input, file_name)
                        else:
                            logger.info("Using AvashowService for non-English TTS")
                            avashow_service.text_to_speech(text_input, file_name)
                    except Exception as tts_error:
                        logger.warning(
                            f"TTS failed, skipping audio generation: {tts_error}"
                        )
                        # Continue without audio if TTS fails
                    if os.path.exists(file_name):
                        logger.info(
                            f"Audio file created: {file_name} (size={os.path.getsize(file_name)} bytes)"
                        )
                    else:
                        logger.warning(
                            f"Expected audio file not found after TTS: {file_name}"
                        )

                    wav_file = os.path.join("audios", f"message_{i}.wav")
                    json_file = os.path.join("audios", f"message_{i}.json")

                    # تبدیل mp3 به wav
                    logger.info(f"Converting {file_name} to {wav_file}")
                    lipsync_service.mp3_to_wav(file_name, wav_file)

                    # تولید lipsync
                    logger.info(f"Generating lipsync for {wav_file}")
                    try:
                        lipsync_service.wav_to_lipsync_json(wav_file, json_file)
                        logger.info(f"Lipsync generated successfully: {json_file}")
                    except Exception as lipsync_error:
                        logger.warning(f"Lipsync generation failed: {lipsync_error}")
                        # Create empty lipsync data as fallback
                        empty_lipsync = {
                            "metadata": {"soundFile": "", "duration": 0},
                            "mouthCues": [],
                        }
                        with open(json_file, "w") as f:
                            import json

                            json.dump(empty_lipsync, f)
                        logger.info(f"Created empty lipsync fallback: {json_file}")

                    # خواندن فایل‌ها
                    try:
                        audio_base64 = file_service.audio_file_to_base64(file_name)
                        lipsync_data = file_service.read_json_transcript(json_file)
                        logger.info(f"Successfully read audio and lipsync files")
                    except Exception as file_error:
                        logger.warning(
                            f"Failed to read audio/lipsync files: {file_error}"
                        )
                        audio_base64 = None
                        lipsync_data = None

                    result_messages.append(
                        Message(
                            text=clean_text_from_json(message.get("text", "")),
                            audio=audio_base64,
                            lipsync=lipsync_data,
                            facialExpression=message.get("facialExpression", "default"),
                            animation=message.get("animation", "Idle"),
                        )
                    )
                    logger.info(f"Message {i} processed successfully with audio")

                    # پاک کردن فایل‌های موقت
                    try:
                        os.remove(file_name)
                        os.remove(wav_file)
                        os.remove(json_file)
                        logger.info(f"Temporary files cleaned up for message {i}")
                    except Exception as e:
                        logger.warning(
                            f"Could not clean up temporary files for message {i}: {e}"
                        )

                except Exception as e:
                    logger.error(f"Error processing message {i} with audio: {e}")
                    # در صورت خطا، پیام بدون audio و lipsync برگردان
                    result_messages.append(
                        Message(
                            text=clean_text_from_json(message.get("text", "")),
                            audio=None,
                            lipsync=None,
                            facialExpression=message.get("facialExpression", "default"),
                            animation=message.get("animation", "Idle"),
                        )
                    )
            else:
                # Skip audio generation for faster response
                logger.info(
                    f"Skipping audio generation for message {i} - can_write_files: {can_write_files}, disable_audio: {disable_audio}"
                )
                result_messages.append(
                    Message(
                        text=clean_text_from_json(message.get("text", "")),
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


@router.post("/test-avashow")
def test_avashow_service(text_input: str):
    """Test the Avashow text-to-speech service"""
    logger.info(f"Testing Avashow service with text: {text_input[:50]}...")

    try:
        avashow_service = AvashowService()

        # Generate a unique filename
        import uuid

        filename = f"test_avashow_{uuid.uuid4().hex[:8]}.mp3"
        file_path = os.path.join("audios", filename)

        # Ensure audios directory exists
        os.makedirs("audios", exist_ok=True)

        # Convert text to speech
        logger.info(f"Converting text to speech and saving to: {file_path}")
        avashow_service.text_to_speech(text_input, file_path)

        # Check if file was created successfully
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            logger.info(
                f"Audio file created successfully: {file_path} (size: {file_size} bytes)"
            )

            return {
                "status": "success",
                "message": "Text converted to speech successfully",
                "input_text": text_input,
                "output_file": filename,
                "file_path": file_path,
                "file_size_bytes": file_size,
                "full_path": os.path.abspath(file_path),
            }
        else:
            logger.error(f"Audio file was not created: {file_path}")
            raise HTTPException(status_code=500, detail="Failed to create audio file")

    except Exception as e:
        logger.error(f"Error testing Avashow service: {e}")
        raise HTTPException(
            status_code=500, detail=f"Avashow service test failed: {str(e)}"
        )


@router.get("/health-detailed")
def detailed_health():
    """Detailed health check with resource monitoring"""
    import psutil
    import os

    status = {
        "status": "running",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "resources": {
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "cpu_percent": psutil.cpu_percent(interval=1),
        },
        "connections": {
            "database": "checking...",
            "openai": "checking...",
            "google_sheets": "checking...",
        },
    }

    # DB connection test
    try:
        from api.database.database import get_db
        from sqlalchemy import text

        db = next(get_db())
        db.execute(text("SELECT 1"))
        status["connections"]["database"] = "connected"
    except Exception as e:
        status["connections"]["database"] = f"not available: {e}"

    # OpenAI test
    try:
        from api.services.openai_service import OpenAIService

        _ = OpenAIService()
        status["connections"]["openai"] = "configured"
    except Exception as e:
        status["connections"]["openai"] = f"error: {e}"

    return status


@router.get("/health")
def health():
    logger.info("Health endpoint called")
    return {"status": "ok", "message": "Backend is running!"}
