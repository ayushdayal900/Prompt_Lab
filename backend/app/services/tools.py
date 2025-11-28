import os
import subprocess
import uuid
import base64
import json
import requests
from pathlib import Path

class FileDownloader:
    def __init__(self, download_dir="downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)

    def download(self, url: str) -> str:
        """Downloads a file from a URL and returns the local path."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Extract filename from URL or headers, fallback to random
            filename = url.split("/")[-1] or f"file_{uuid.uuid4().hex}"
            # Clean filename
            filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in "._-"])
            
            local_path = self.download_dir / filename
            
            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return str(local_path.absolute())
        except Exception as e:
            return f"Error downloading file: {e}"

class CodeExecutor:
    def __init__(self, work_dir="workspace"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(exist_ok=True)

    def execute(self, code: str) -> str:
        """Writes code to a file and executes it in a subprocess."""
        # Security Warning: This executes arbitrary code.
        # In a real prod env, this should be sandboxed (Docker/Firecracker).
        
        filename = f"script_{uuid.uuid4().hex}.py"
        filepath = self.work_dir / filename
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code)
            
            # Execute
            result = subprocess.run(
                ["python", str(filepath)],
                capture_output=True,
                text=True,
                timeout=30, # 30s timeout
                cwd=self.work_dir
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
                
            return output
        except subprocess.TimeoutExpired:
            return "Error: Execution timed out (30s limit)."
        except Exception as e:
            return f"Error executing code: {e}"

class VisionHelper:
    @staticmethod
    def encode_image(image_path: str) -> str:
        """Encodes an image to base64."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            return None
