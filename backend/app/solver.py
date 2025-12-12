import asyncio
import time
import json
import logging
import traceback
from app.browser import AsyncBrowser
from app.llm import ask_llm
from app.utils import CodeExecutor, FileDownloader, extract_text_from_image, transcribe_audio
from app.models import LLMAction

logger = logging.getLogger(__name__)

class Solver:
    def __init__(self, email: str, secret: str, api_token: str = None):
        self.email = email
        self.secret = secret
        # ... (rest of init)
        self.api_token = api_token 
        # api_token handled via env vars in llm.py usually, but can pass if needed
        self.browser = AsyncBrowser()
        self.executor = CodeExecutor()
        self.downloader = FileDownloader()
        self.history = []

    async def solve(self, start_url: str, deadline: float):
        try:
            await self.browser.start()
            current_url = start_url
            
            # Additional constraint: The submission URL is likely constant for this specific quiz
            DEFAULT_SUBMIT_URL = "https://tds-llm-analysis.s-anand.net/submit"

            while current_url and time.time() < deadline:
                logger.info(f"Visiting {current_url} | Time left: {deadline - time.time():.1f}s")
                
                # 1. Load Page
                try:
                    html_content = await self.browser.load_page(current_url)
                    text_content = await self.browser.get_text_content()
                    links = await self.browser.extract_links()
                except Exception as e:
                    logger.error(f"Failed to load page: {e}")
                    break

                # 2. Analyze with LLM
                prompt = (
                    f"You are solving a quiz. Current URL: {current_url}\n"
                    f"Page Text:\n{text_content[:8000]}\n"
                    f"Links:\n{str(links)[:2000]}\n"
                    "Analyze the page. If there is a question, solve it. "
                    "If you need to download a file or run code, do so. "
                    "If you have the answer, submit it. "
                    "Provide your response as a valid JSON object matching the LLMAction schema."
                )

                system_prompt = (
                     "You are an autonomous solver agent. Available actions: "
                     "'code' (run python), 'download' (url), 'submit' (submit answer), 'wait'. "
                     "Return JSON ONLY. "
                     f"IMPORTANT: The submission URL is almost always '{DEFAULT_SUBMIT_URL}'. "
                     "Use that unless the page explicitly says otherwise. "
                     "If the page says 'Start by POSTing', your FIRST action should be to 'submit'. "
                     "For the start step, the 'answer' is typically an empty string."
                )
                
                max_retries = 3
                action_data = None
                
                for _ in range(max_retries):
                    response_text = await ask_llm(prompt, self.history, system_prompt)
                    try:
                        # loose json parsing
                        clean_text = response_text.strip().replace("```json", "").replace("```", "")
                        data = json.loads(clean_text)
                        # Validate with pydantic
                        action_data = LLMAction(**data)
                        break
                    except Exception as e:
                        logger.warning(f"Failed to parse LLM response: {e}. Retrying...")
                
                if not action_data:
                    logger.error("LLM failed to produce valid action.")
                    break

                logger.info(f"LLM Action: {action_data.action}")
                
                # 3. Execute Action
                if action_data.action == "code":
                    output = self.executor.execute(action_data.code)
                    self.history.append({"role": "user", "content": f"Code Output: {output}"})
                
                elif action_data.action == "download":
                    path = self.downloader.download(action_data.url)
                    content = f"File downloaded to {path}"
                    logger.info(f"Downloaded file: {path}")

                    # Handle Images
                    if path.endswith(".png") or path.endswith(".jpg"):
                         ocr_text = extract_text_from_image(path)
                         content += f"\nOCR Content: {ocr_text}"
                    
                    # Handle Audio with Transcription
                    # Heuristic: Check extension OR if the task itself is an audio task
                    is_audio_task = "audio" in current_url.lower()
                    if path.endswith(".mp3") or path.endswith(".wav") or is_audio_task:
                         logger.info(f"Transcribing audio file: {path} (Task audio: {is_audio_task})")
                         transcript = transcribe_audio(path)
                         content += f"\n[AUDIO TRANSCRIPT]: {transcript}"
                         logger.info(f"Transcription result: {transcript[:50]}...")
                    
                    # Add to history so LLM knows it's done
                    self.history.append({"role": "user", "content": content})
                    
                    # CRITICAL: Force a small sleep or state change so we don't hammer the LLM 
                    # causing rate limits in a tight loop if it decides to download again.
                    await asyncio.sleep(2)

                elif action_data.action == "submit":
                    # Construct submission
                    submit_url = action_data.submit_url
                    
                    # Heuristic: Default to known submit URL if none provided or if it looks relative/wrong
                    if not submit_url or "http" not in submit_url:
                        submit_url = DEFAULT_SUBMIT_URL

                    import aiohttp
                    payload = {
                        "email": self.email,
                        "secret": self.secret,
                        "url": current_url, # The quiz URL we are solving
                        "answer": action_data.answer if action_data.answer is not None else ""
                    }
                    
                    # Retry logic for "Missing field answer" (heuristics)
                    candidates = [payload["answer"]] # Start with what LLM gave
                    if payload["answer"] == "":
                        candidates.extend([self.email, "start", "0"]) # Fallbacks
                    
                    success = False
                    for ans_candidate in candidates:
                        payload["answer"] = ans_candidate
                        logger.info(f"Submitting to {submit_url}: {payload}")
                        
                        async with aiohttp.ClientSession() as session:
                            async with session.post(submit_url, json=payload) as resp:
                                try:
                                    result = await resp.json()
                                except Exception as e:
                                    text_resp = await resp.text()
                                    result = {"error": f"Failed to parse JSON response: {text_resp[:200]}"}

                                logger.info(f"Submission Result: {result}")
                                
                                if result.get("correct"):
                                    next_url = result.get("next") or result.get("url")
                                    if next_url:
                                        current_url = next_url
                                        self.history = [] 
                                    else:
                                        logger.info("Quiz finished successfully! (No next URL returned)")
                                        return
                                    success = True
                                    break # Exit candidate loop
                                
                                # If error is specifically about missing answer, try next candidate
                                if str(result.get("error")).lower() == "missing field answer":
                                    logger.warning(f"Got 'Missing field answer' for '{ans_candidate}'. Retrying with next candidate...")
                                    continue
                                else:
                                    # Real wrong answer or other error
                                    self.history.append({"role": "user", "content": f"Wrong answer. Server said: {result}"})
                                    break # Don't try other candidates if it's just 'wrong' logic
                    
                    if success:
                        continue # Move to next main loop iteration

                
                elif action_data.action == "wait":
                    logger.info("LLM decided to wait.")
                    break

        except Exception as e:
            logger.error(f"Solver crashed: {traceback.format_exc()}")
            # Never crash the server, just log
        finally:
            await self.browser.close()
