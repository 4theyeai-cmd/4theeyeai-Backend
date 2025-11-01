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
import requests

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


def cleanup_temp_files(session_id: str = None):
    """Clean up temporary message files from audios directory"""
    try:
        import glob

        if session_id:
            # Clean up files for specific session
            session_suffix = (
                session_id.split("_")[-1] if "_" in session_id else session_id[-8:]
            )
            temp_patterns = [
                f"audios/message_{session_suffix}_*.mp3",
                f"audios/message_{session_suffix}_*.wav",
                f"audios/message_{session_suffix}_*.json",
            ]
            logger.info(f"🧹 Cleaning up files for session: {session_suffix}")
        else:
            # Clean up all temporary message files
            temp_patterns = [
                "audios/message_*.mp3",
                "audios/message_*.wav",
                "audios/message_*.json",
            ]
            logger.info("🧹 Cleaning up all temporary message files")

        cleaned_files = []
        for pattern in temp_patterns:
            files = glob.glob(pattern)
            for file_path in files:
                try:
                    # Skip permanent files (like introduction, errorMessage, etc.)
                    filename = os.path.basename(file_path)
                    if filename.startswith(
                        ("introduction", "errorMessage", "intro_", "api_")
                    ):
                        continue

                    os.remove(file_path)
                    cleaned_files.append(file_path)
                    logger.info(f"🗑️ Cleaned up temp file: {file_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not remove {file_path}: {e}")

        if cleaned_files:
            logger.info(f"✅ Cleaned up {len(cleaned_files)} temporary files")
        else:
            logger.info("ℹ️ No temporary files to clean up")

    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")


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
        logger.info("=" * 80)
        logger.info("🚀 STARTING /intro")
        logger.info("=" * 80)
        # Basic environment diagnostics to trace permission issues
        try:
            cwd = os.getcwd()
            logger.info(f"CWD: {cwd}")
            logger.info(f"Absolute CWD: {os.path.abspath(cwd)}")
        except Exception as env_err:
            logger.warning(f"Could not get CWD: {env_err}")

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
            logger.info(f"Converting MP3 to WAV for intro: {mp3_file} -> {wav_file}")
            try:
                lipsync_service.mp3_to_wav(mp3_file, wav_file)
            except PermissionError as pe:
                logger.error(f"PermissionError during ffmpeg conversion: {pe}")
                logger.error(f"mp3 path: {mp3_file}, wav path: {wav_file}")
                # Surface the exact error
                raise HTTPException(
                    status_code=500, detail=f"ffmpeg permission error: {pe}"
                )
            except Exception as conv_err:
                logger.error(f"Error during MP3->WAV conversion: {conv_err}")
                raise

        # Generate lipsync json
        logger.info(f"Generating lip-sync JSON for intro: {wav_file} -> {json_file}")
        try:
            # Pre-flight diagnostics for rhubarb location/permissions
            try:
                candidate = os.path.abspath(os.path.join(os.getcwd(), "bin", "rhubarb"))
                if os.path.exists(candidate):
                    st = os.stat(candidate)
                    logger.info(
                        f"rhubarb candidate: {candidate}, mode: {oct(st.st_mode)}, size: {st.st_size}"
                    )
                    logger.info(
                        f"os.access(X_OK)={os.access(candidate, os.X_OK)}, os.access(R_OK)={os.access(candidate, os.R_OK)}"
                    )
                else:
                    logger.info(f"rhubarb candidate not found at: {candidate}")
            except Exception as diag_err:
                logger.warning(f"Failed pre-flight rhubarb diagnostics: {diag_err}")

            lipsync_service.wav_to_lipsync_json(wav_file, json_file)
        except PermissionError as pe:
            logger.error(f"PermissionError during rhubarb execution: {pe}")
            logger.error(f"wav path: {wav_file}, json path: {json_file}")
            raise HTTPException(
                status_code=500, detail=f"rhubarb permission error: {pe}"
            )
        except Exception as lipsync_err:
            logger.error(f"Error generating lip-sync JSON: {lipsync_err}")
            raise

        # Read back audio and json
        audio_base64 = file_service.audio_file_to_base64(mp3_file)
        lipsync_data = file_service.read_json_transcript(json_file)

        text = (
            "Hello, I am Binad, the AI CIP assistant for Imam Khomeini Airport and Mashhad, and I am ready to help you with CIP reservations or CIP services."
            if is_english
            else "سلام! من نکسا هستم، دستیار هوش مصنوعی CIP فرودگاه امام خمینی و مشهد. آماده‌ام تا در مورد رزرو یا خدمات CIP به شما کمک کنم."
        )

        message = Message(
            text=text,
            audio=audio_base64,
            lipsync=lipsync_data,
            facialExpression="smile",
            animation="StandingStandingIdle",  # "Talking_1",
        )

        logger.info("✅ /intro completed successfully")
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


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    logger.info("=" * 100)
    logger.info("🚀 STARTING /chat ENDPOINT")
    logger.info("=" * 100)

    # Clean up any existing temporary files for this session before processing
    logger.info(
        f"🧹 Cleaning up previous temporary files for session: {request.session_id}"
    )
    cleanup_temp_files(request.session_id)

    # Log incoming request details
    logger.info(f"📝 Incoming Request Details:")
    logger.info(f"   - Message: '{request.message}'")
    logger.info(f"   - Session ID: '{request.session_id}'")
    logger.info(f"   - Language: '{request.language}'")
    logger.info(f"   - Request Type: {type(request)}")
    logger.info(
        f"   - Request Dict: {request.dict() if hasattr(request, 'dict') else 'N/A'}"
    )

    # Initialize services
    logger.info("🔧 Initializing Services:")
    try:
        openai_service = OpenAIService()
        logger.info("   ✅ OpenAIService initialized")

        avashow_service = AvashowService()
        logger.info("   ✅ AvashowService initialized")

        elevenlabs_service = ElevenLabsService()
        logger.info("   ✅ ElevenLabsService initialized")

        lipsync_service = LipSyncService()
        logger.info("   ✅ LipSyncService initialized")

        file_service = FileService()
        logger.info("   ✅ FileService initialized")

        api_key = get_avashow_api_key()
        logger.info(f"   ✅ Avashow API Key: {'Present' if api_key else 'Missing'}")

    except Exception as service_error:
        logger.error(f"❌ Service initialization failed: {service_error}")
        raise HTTPException(
            status_code=500,
            detail=f"Service initialization failed: {str(service_error)}",
        )

    # Check for empty message
    if not request.message:
        logger.info("📭 No message provided, returning default messages")
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
    logger.info("🔑 Validating API Keys:")
    is_english = (request.language or "").lower().startswith("en")
    logger.info(f"   - Language: '{request.language}' -> Is English: {is_english}")

    openai_key = os.getenv("OPENAI_API_KEY")
    logger.info(f"   - OpenAI API Key: {'Present' if openai_key else 'Missing'}")
    logger.info(f"   - Avashow API Key: {'Present' if api_key else 'Missing'}")

    if (not openai_key) or (not is_english and not api_key):
        logger.warning("❌ API keys missing for the requested operation")
        logger.warning(f"   - OpenAI Key Missing: {not openai_key}")
        logger.warning(
            f"   - Avashow Key Missing (for non-English): {not is_english and not api_key}"
        )
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
        logger.info("🤖 Calling OpenAI Service:")
        logger.info(f"   - Message: '{request.message}'")
        logger.info(f"   - Session ID: '{request.session_id}'")
        logger.info(f"   - Language: '{request.language}'")

        openai_messages: list = openai_service.get_assistant_response(
            request.message, request.session_id, request.language
        )

        logger.info(f"✅ OpenAI Service Response:")
        logger.info(
            f"   - Messages Count: {len(openai_messages) if openai_messages else 0}"
        )
        logger.info(f"   - Messages Type: {type(openai_messages)}")
        logger.info(f"   - Messages Content: {openai_messages}")

        result_messages = []

        # استفاده از مسیر قابل نوشتن
        logger.info("📁 Setting up Audio Directory:")
        audio_dir = get_temp_audio_dir()
        logger.info(f"   - Audio Directory: {audio_dir}")
        logger.info(f"   - Directory Absolute Path: {os.path.abspath(audio_dir)}")

        # بررسی قابلیت نوشتن در مسیر
        logger.info("✍️ Testing File Write Permissions:")
        can_write_files = True
        try:
            test_file = os.path.join(audio_dir, "test_write.tmp")
            logger.info(f"   - Test File Path: {test_file}")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            logger.info("   ✅ Write permissions confirmed")
        except Exception as e:
            logger.warning(f"   ❌ Cannot write files to {audio_dir}: {e}")
            can_write_files = False

        logger.info("🔄 Processing Messages:")
        logger.info(
            f"   - Total Messages to Process: {len(openai_messages) if openai_messages else 0}"
        )

        for i, message in enumerate(openai_messages or []):
            logger.info(
                f"📝 Processing Message {i + 1}/{len(openai_messages) if openai_messages else 0}:"
            )
            logger.info(f"   - Message Type: {type(message)}")
            logger.info(f"   - Message Content: {message}")

            try:
                text_value = (
                    message.get("text") if isinstance(message, dict) else str(message)
                )
                logger.info(f"   - Extracted Text: '{text_value}'")
            except Exception as extract_error:
                text_value = str(message)
                logger.warning(f"   - Text extraction failed: {extract_error}")
                logger.info(f"   - Fallback Text: '{text_value}'")

            logger.info(
                f"   - Final Text Value: '{text_value if text_value else 'No text'}'"
            )

            # Check if this is an error response from the external service
            is_error_response = (
                isinstance(message, dict)
                and message.get("text") == "ERROR_SERVICE_UNAVAILABLE"
                and message.get("is_error", False)
            )

            if is_error_response:
                logger.info("🚨 Processing ERROR response from external service")
                error_language = message.get("language", "fa")
                logger.info(f"   - Error Language: {error_language}")

                # Determine error audio file based on language
                if error_language.lower().startswith("en"):
                    error_audio_file = "audios/errorMessage_en.mp3"
                    error_text_file = "audios/errorMessage_en.txt"
                    logger.info("   - Using English error message")
                else:
                    error_audio_file = "audios/errorMessage.mp3"
                    error_text_file = "audios/errorMessage.txt"
                    logger.info("   - Using Persian error message")

                # Read error text
                try:
                    with open(error_text_file, "r", encoding="utf-8") as f:
                        error_text = f.read().strip()
                    logger.info(f"   - Error Text: '{error_text}'")
                except Exception as e:
                    logger.error(f"   - Failed to read error text file: {e}")
                    error_text = "خطا در دریافت پاسخ از سرور"

                # Create error message with audio and lipsync
                try:
                    if os.path.exists(error_audio_file):
                        logger.info(f"   - Error audio file found: {error_audio_file}")

                        # Convert MP3 to WAV for lipsync
                        error_wav_file = error_audio_file.replace(".mp3", ".wav")
                        error_json_file = error_audio_file.replace(".mp3", ".json")

                        logger.info(
                            f"   - Converting error audio to WAV: {error_wav_file}"
                        )
                        lipsync_service.mp3_to_wav(error_audio_file, error_wav_file)

                        logger.info(f"   - Generating error lipsync: {error_json_file}")
                        lipsync_service.wav_to_lipsync_json(
                            error_wav_file, error_json_file
                        )

                        # Read audio and lipsync data
                        audio_base64 = file_service.audio_file_to_base64(
                            error_audio_file
                        )
                        lipsync_data = file_service.read_json_transcript(
                            error_json_file
                        )

                        logger.info(
                            "   ✅ Error message with audio and lipsync created successfully"
                        )

                        error_message = Message(
                            text=error_text,
                            audio=audio_base64,
                            lipsync=lipsync_data,
                            facialExpression="sad",
                            animation="Sad",
                        )

                        result_messages.append(error_message)
                        logger.info(f"   ✅ Error message {i + 1} added to response")
                        continue  # Skip normal processing for this message
                    else:
                        logger.warning(
                            f"   - Error audio file not found: {error_audio_file}"
                        )
                except Exception as e:
                    logger.error(f"   - Failed to process error audio: {e}")

                # Fallback: create error message without audio
                fallback_error_message = Message(
                    text=error_text,
                    audio=None,
                    lipsync=None,
                    facialExpression="sad",
                    animation="Sad",
                )
                result_messages.append(fallback_error_message)
                logger.info(f"   ✅ Fallback error message {i + 1} added to response")
                continue  # Skip normal processing for this message

            if can_write_files:
                logger.info(f"   🎵 Audio Processing Enabled for Message {i + 1}")
                try:
                    # Ensure audios directory exists
                    logger.info(f"   📁 Ensuring audios directory exists")
                    os.makedirs("audios", exist_ok=True)

                    # Create unique filename with session ID to prevent conflicts
                    session_suffix = (
                        request.session_id.split("_")[-1]
                        if "_" in request.session_id
                        else request.session_id[-8:]
                    )
                    file_name = os.path.join(
                        "audios", f"message_{session_suffix}_{i}.mp3"
                    )
                    logger.info(f"   📄 Target Audio File: {file_name}")
                    logger.info(f"   🔑 Session Suffix: {session_suffix}")

                    text_input = (
                        message.get("text", "")
                        if isinstance(message, dict)
                        else str(message)
                    )
                    logger.info(
                        f"   📝 Text Input for TTS: '{text_input[:100]}{'...' if len(text_input) > 100 else ''}'"
                    )

                    # تبدیل متن به گفتار - انتخاب سرویس بر اساس زبان
                    logger.info(f"   🔊 Converting text to speech:")
                    logger.info(
                        f"      - Language: {'English' if is_english else 'Non-English'}"
                    )
                    logger.info(f"      - Text Length: {len(text_input)} characters")

                    try:
                        if is_english:
                            logger.info(
                                "      - Using ElevenLabsService for English TTS"
                            )
                            elevenlabs_service.text_to_speech(text_input, file_name)
                        else:
                            logger.info(
                                "      - Using AvashowService for non-English TTS"
                            )
                            avashow_service.text_to_speech(text_input, file_name)
                        logger.info("      ✅ TTS conversion completed")
                    except Exception as tts_error:
                        logger.warning(f"      ❌ TTS failed: {tts_error}")
                        logger.warning(
                            f"      - Error Type: {type(tts_error).__name__}"
                        )
                        logger.warning(
                            f"      - Skipping audio generation for this message"
                        )
                        # Continue without audio if TTS fails

                    # Check if audio file was created
                    if os.path.exists(file_name):
                        file_size = os.path.getsize(file_name)
                        logger.info(f"      ✅ Audio file created successfully:")
                        logger.info(f"         - File: {file_name}")
                        logger.info(f"         - Size: {file_size} bytes")
                        logger.info(
                            f"         - Absolute Path: {os.path.abspath(file_name)}"
                        )
                    else:
                        logger.warning(
                            f"      ❌ Expected audio file not found after TTS: {file_name}"
                        )

                    wav_file = os.path.join(
                        "audios", f"message_{session_suffix}_{i}.wav"
                    )
                    json_file = os.path.join(
                        "audios", f"message_{session_suffix}_{i}.json"
                    )
                    logger.info(f"   📄 Lip Sync Files:")
                    logger.info(f"      - WAV File: {wav_file}")
                    logger.info(f"      - JSON File: {json_file}")

                    # تبدیل mp3 به wav
                    logger.info(f"   🔄 Converting MP3 to WAV:")
                    logger.info(f"      - Source: {file_name}")
                    logger.info(f"      - Target: {wav_file}")
                    try:
                        lipsync_service.mp3_to_wav(file_name, wav_file)
                        logger.info(f"      ✅ MP3 to WAV conversion completed")

                        # Check WAV file
                        if os.path.exists(wav_file):
                            wav_size = os.path.getsize(wav_file)
                            logger.info(f"      - WAV file size: {wav_size} bytes")
                        else:
                            logger.warning(f"      ❌ WAV file not created: {wav_file}")
                    except Exception as wav_error:
                        logger.error(
                            f"      ❌ MP3 to WAV conversion failed: {wav_error}"
                        )

                    # تولید lipsync
                    logger.info(f"   🎭 Generating Lip Sync:")
                    logger.info(f"      - Source WAV: {wav_file}")
                    logger.info(f"      - Target JSON: {json_file}")
                    try:
                        lipsync_service.wav_to_lipsync_json(wav_file, json_file)
                        logger.info(f"      ✅ Lip sync generation completed")

                        # Check JSON file
                        if os.path.exists(json_file):
                            json_size = os.path.getsize(json_file)
                            logger.info(f"      - JSON file size: {json_size} bytes")
                        else:
                            logger.warning(
                                f"      ❌ JSON file not created: {json_file}"
                            )
                    except Exception as lipsync_error:
                        logger.error(
                            f"      ❌ Lip sync generation failed: {lipsync_error}"
                        )

                    # خواندن فایل‌ها
                    logger.info(f"   📖 Reading Generated Files:")
                    try:
                        audio_base64 = file_service.audio_file_to_base64(file_name)
                        logger.info(
                            f"      ✅ Audio file converted to base64 (length: {len(audio_base64) if audio_base64 else 0})"
                        )
                    except Exception as audio_error:
                        logger.error(
                            f"      ❌ Audio base64 conversion failed: {audio_error}"
                        )
                        audio_base64 = None

                    try:
                        lipsync_data = file_service.read_json_transcript(json_file)
                        logger.info(f"      ✅ Lip sync data read successfully")
                        logger.info(f"      - Lip sync data type: {type(lipsync_data)}")
                        logger.info(
                            f"      - Lip sync data length: {len(str(lipsync_data)) if lipsync_data else 0}"
                        )
                    except Exception as lipsync_read_error:
                        logger.error(
                            f"      ❌ Lip sync data reading failed: {lipsync_read_error}"
                        )
                        lipsync_data = None

                    # Create final message
                    logger.info(f"   📝 Creating Final Message:")
                    cleaned_text = clean_text_from_json(message.get("text", ""))
                    facial_expression = (
                        message.get("facialExpression", "default")
                        if isinstance(message, dict)
                        else "default"
                    )
                    animation = (
                        message.get("animation", "StandingIdle")
                        if isinstance(message, dict)
                        and message.get("animation") is not None
                        else "StandingIdle"
                    )

                    logger.info(
                        f"      - Cleaned Text: '{cleaned_text[:100]}{'...' if len(cleaned_text) > 100 else ''}'"
                    )
                    logger.info(f"      - Facial Expression: '{facial_expression}'")
                    logger.info(f"      - Animation: '{animation}'")
                    logger.info(f"      - Audio Present: {audio_base64 is not None}")
                    logger.info(f"      - Lip Sync Present: {lipsync_data is not None}")

                    final_message = Message(
                        text=cleaned_text,
                        audio=audio_base64,
                        lipsync=lipsync_data,
                        facialExpression=facial_expression,
                        animation=animation,
                    )

                    result_messages.append(final_message)
                    logger.info(
                        f"   ✅ Message {i + 1} processed successfully with audio"
                    )

                    # پاک کردن فایل‌های موقت
                    try:
                        if os.path.exists(file_name):
                            os.remove(file_name)
                            logger.info(f"   🗑️ Cleaned up MP3 file: {file_name}")
                        if os.path.exists(wav_file):
                            os.remove(wav_file)
                            logger.info(f"   🗑️ Cleaned up WAV file: {wav_file}")
                        if os.path.exists(json_file):
                            os.remove(json_file)
                            logger.info(f"   🗑️ Cleaned up JSON file: {json_file}")
                        logger.info(
                            f"   ✅ Temporary files cleaned up for message {i + 1}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"   ⚠️ Could not clean up temporary files for message {i + 1}: {e}"
                        )

                except Exception as e:
                    logger.error(
                        f"   ❌ Error processing message {i + 1} with audio: {e}"
                    )
                    logger.error(f"      - Error Type: {type(e).__name__}")
                    logger.error(f"      - Error Details: {str(e)}")
                    logger.info(f"      - Creating fallback message without audio")

                    # در صورت خطا، پیام بدون audio و lipsync برگردان
                    fallback_message = Message(
                        text=clean_text_from_json(message.get("text", "")),
                        audio=None,
                        lipsync=None,
                        facialExpression=(
                            message.get("facialExpression", "default")
                            if isinstance(message, dict)
                            else "default"
                        ),
                        animation=(
                            message.get("animation", "StandingIdle")
                            if isinstance(message, dict)
                            and message.get("animation") is not None
                            else "StandingIdle"
                        ),
                    )
                    result_messages.append(fallback_message)
                    logger.info(f"   ✅ Fallback message {i + 1} created successfully")
            else:
                logger.info(
                    f"   📝 File Writing Disabled - Creating Text-Only Message {i + 1}"
                )
                # Create message without audio when file writing is disabled
                text_only_message = Message(
                    text=clean_text_from_json(message.get("text", "")),
                    audio=None,
                    lipsync=None,
                    facialExpression=(
                        message.get("facialExpression", "default")
                        if isinstance(message, dict)
                        else "default"
                    ),
                    animation=(
                        message.get("animation", "StandingIdle")
                        if isinstance(message, dict)
                        and message.get("animation") is not None
                        else "StandingIdle"
                    ),
                )
                result_messages.append(text_only_message)
                logger.info(f"   ✅ Text-only message {i + 1} created successfully")

        logger.info("=" * 100)
        logger.info("🎉 CHAT ENDPOINT COMPLETED SUCCESSFULLY")
        logger.info("=" * 100)
        logger.info(f"📊 Final Results:")
        logger.info(f"   - Total Messages Processed: {len(result_messages)}")
        logger.info(
            f"   - Messages with Audio: {sum(1 for msg in result_messages if msg.audio is not None)}"
        )
        logger.info(
            f"   - Messages with Lip Sync: {sum(1 for msg in result_messages if msg.lipsync is not None)}"
        )
        logger.info(f"   - File Write Enabled: {can_write_files}")
        logger.info(f"   - Audio Directory: {audio_dir}")

        # Log summary of each message
        for i, msg in enumerate(result_messages):
            logger.info(f"   📝 Message {i + 1}:")
            logger.info(f"      - Text Length: {len(msg.text) if msg.text else 0}")
            logger.info(f"      - Has Audio: {msg.audio is not None}")
            logger.info(f"      - Has Lip Sync: {msg.lipsync is not None}")
            logger.info(f"      - Facial Expression: {msg.facialExpression}")
            logger.info(f"      - Animation: {msg.animation}")

        # Final cleanup of any remaining temporary files for this session
        logger.info(
            f"🧹 Final cleanup of temporary files for session: {request.session_id}"
        )
        cleanup_temp_files(request.session_id)

        return ChatResponse(messages=result_messages)

    except Exception as e:
        logger.error("=" * 100)
        logger.error("💥 CHAT ENDPOINT FAILED")
        logger.error("=" * 100)
        logger.error(f"❌ Error Details:")
        logger.error(f"   - Error Type: {type(e).__name__}")
        logger.error(f"   - Error Message: {str(e)}")
        logger.error(f"   - Error Args: {e.args if hasattr(e, 'args') else 'N/A'}")
        logger.error(
            f"   - Request Message: '{request.message if 'request' in locals() else 'N/A'}'"
        )
        logger.error(
            f"   - Request Session ID: '{request.session_id if 'request' in locals() else 'N/A'}'"
        )
        logger.error(
            f"   - Request Language: '{request.language if 'request' in locals() else 'N/A'}'"
        )

        # Clean up temporary files even if there was an error
        logger.info(
            f"🧹 Cleaning up temporary files after error for session: {request.session_id}"
        )
        cleanup_temp_files(request.session_id)

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


@router.get("/health")
def health():
    logger.info("Health endpoint called")
    return {"status": "ok", "message": "Backend is running!"}
