import subprocess
import platform

async def speak_completion(message: str, language: str = "en"):
    """
    Speak completion message using macOS native TTS (say command)
    
    This is much faster and simpler than gTTS, and works offline.
    macOS say command supports multiple voices and languages.
    
    Args:
        message: The message to speak
        language: Language code (currently only 'en' is used, but kept for compatibility)
    """
    
    try:
        # Only use TTS on macOS
        if platform.system() != "Darwin":
            print(f"⚠️ TTS only supported on macOS. Message: '{message}'")
            return
        
        print(f"🗣️ Speaking: '{message}'")
        
        # Use macOS say command - fast and native
        # Run in background so it doesn't block
        subprocess.Popen(["say", message], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("✅ TTS initiated")
        
    except Exception as e:
        print(f"⚠️ TTS Error: {e}")
