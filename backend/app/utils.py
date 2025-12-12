import os
import requests
import subprocess
import aiohttp
import uuid
import base64
from typing import List

class FileDownloader:
    def __init__(self, download_dir="downloads"):
        self.download_dir = download_dir
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

    def download(self, url: str) -> str:
        try:
            filename = os.path.basename(url.split("?")[0])
            if not filename:
                filename = f"file_{uuid.uuid4()}"
            
            # Simple extension check basic fix
            if "." not in filename:
                filename += ".dat"

            path = os.path.join(self.download_dir, filename)
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return path
        except Exception as e:
            return f"Error downloading: {e}"

class CodeExecutor:
    def __init__(self):
        pass

    def execute(self, code: str) -> str:
        """
        Executes Python code in a separate subprocess.
        Security Warning: This executes arbitrary code.
        """
        try:
            # Wrap code to print last expression if it's not a print statement
            # (Simple heuristic)
            
            result = subprocess.run(
                ["python", "-c", code],
                capture_output=True,
                text=True,
                timeout=10, # 10s timeout for code execution
                cwd=os.getcwd()
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nStderr: {result.stderr}"
            
            return output
        except subprocess.TimeoutExpired:
            return "Execution timed out."
        except Exception as e:
            return f"Execution error: {e}"

# Placeholder for image OCR and PDF extraction
# In a real scenario, we'd use 'pytesseract' and 'PyPDF2'
# For now, we'll keep them simple or assume libraries are installed if requested.

try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


def extract_text_from_image(image_path: str) -> str:
    if not HAS_OCR:
        return "OCR library not installed."
    try:
        return pytesseract.image_to_string(Image.open(image_path))
    except Exception as e:
        return f"OCR Error: {e}"

def transcribe_audio(audio_path: str) -> str:
    """
    Transcribes audio using OpenAI's Whisper API.
    Auto-converts .opus or other formats to .mp3 first if needed.
    """
    try:
        # Ensure ffmpeg is available via static_ffmpeg
        import static_ffmpeg
        import subprocess
        static_ffmpeg.add_paths()
        
        from openai import OpenAI
        
        # Convert to mp3 if needed (OpenAI doesn't like some raw opus containers or just to be safe)
        if audio_path.endswith(".opus") or audio_path.endswith(".ogg") or audio_path.endswith(".wav"):
            # Use WAV instead of MP3 to avoid encoding issues with Whisper
            wav_path = audio_path + ".wav"
            import logging 
            logger = logging.getLogger(__name__)
            logger.info(f"Converting {audio_path} to {wav_path} using ffmpeg...")
            
            # cmd: ffmpeg -i input.opus -ar 16000 -ac 1 -c:a pcm_s16le -y output.wav
            # 16kHZ mono PCM is the most compatible format for Whisper
            cmd = ["ffmpeg", "-i", audio_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", "-y", wav_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Log ffmpeg output even on success to see if there were warnings
            if result.stderr:
                logger.info(f"FFmpeg stderr: {result.stderr[:200]}...") 

            if result.returncode != 0:
                logger.error(f"FFmpeg conversion failed: {result.stderr}")
                return f"Audio Conversion Error: {result.stderr}"
                
            audio_path = wav_path
        
        # Use direct HTTP request to handle AIPipe proxy quirks with multipart/form-data
        import requests
        
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        # Ensure base_url doesn't end with slash
        base_url = base_url.rstrip("/")
        
        url = f"{base_url}/audio/transcriptions"
        
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # data contains the 'model' field which AIPipe demands
        data = {
            "model": "whisper-1",
            "response_format": "text"
        }
        
        # files contains the audio file
        # ensure we open strictly as binary
        with open(audio_path, "rb") as f:
            files = {
                "file": ("audio.wav", f, "audio/wav")
            }
            
            logger.info(f"Posting audio to {url} with model=whisper-1")
            response = requests.post(url, headers=headers, data=data, files=files)
            
        if response.status_code == 200:
            return response.text
        else:
            logger.error(f"Transcription failed: {response.text}")
            return f"Transcription Error: {response.status_code} - {response.text}"

    except Exception as e:
        import traceback
        error_detail = str(e)
        print(f"CRITICAL TRANSCRIPTION ERROR: {error_detail}") 
        return f"Transcription Error: {error_detail}"

