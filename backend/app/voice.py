from fastapi import APIRouter, UploadFile, HTTPException
import whisper
import tempfile
import os

router = APIRouter()

# Load Whisper model (small) from local path
try:
    model = whisper.load_model("small", download_root="models/whisper")
    print("✅ Whisper model loaded successfully")
except Exception as e:
    print(f"⚠️ Whisper model not loaded: {e}")
    model = None

@router.post("/api/voice/transcribe")
async def transcribe_audio(audio: UploadFile):
    """
    Transcribe audio to text in the ORIGINAL language script
    
    Supports 99+ languages including:
    - Hindi (हिंदी), Tamil (தமிழ்), Telugu (తెలుగు), Bengali (বাংলা)
    - Marathi (मराठी), Gujarati (ગુજરાતી), Kannada (ಕನ್ನಡ)
    - Malayalam (മലയാളം), Punjabi (ਪੰਜਾਬੀ), Odia (ଓଡ଼ିଆ)
    - English and many more
    
    IMPORTANT: Transcribes in the original script WITHOUT translation
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Whisper model not available")
    
    # Save uploaded audio to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        content = await audio.read()
        temp_audio.write(content)
        temp_path = temp_audio.name
    
    try:
        # Transcribe with automatic language detection
        # CRITICAL: Do NOT set task="translate" - this keeps original script
        result = model.transcribe(
            temp_path,
            language=None,  # Auto-detect language
            task="transcribe",  # TRANSCRIBE (not translate) - keeps original script
            fp16=False  # Better compatibility
        )
        
        detected_language = result.get("language", "unknown")
        transcribed_text = result["text"].strip()
        
        print(f"🎤 Transcribed ({detected_language}): '{transcribed_text}'")
        
        return {
            "text": transcribed_text,
            "language": detected_language,
            "segments": result.get("segments", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
