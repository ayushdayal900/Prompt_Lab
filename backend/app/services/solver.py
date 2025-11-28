import asyncio
import json
import re
import os
from playwright.async_api import async_playwright
import aiohttp
from openai import AsyncOpenAI
from app.services.tools import FileDownloader, CodeExecutor

class QuizSolver:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.downloader = FileDownloader()
        self.executor = CodeExecutor()

    async def start_browser(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def close_browser(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def analyze_with_llm(self, content: str, history: list, api_token: str) -> dict:
        """
        Uses LLM to decide the next action based on page content and history.
        """
        if not api_token:
            return None

        try:
            client = AsyncOpenAI(
                api_key=api_token,
                base_url="https://openrouter.ai/api/v1"
            )

            system_prompt = """
            You are an autonomous data science agent. You need to solve a quiz level.
            You have access to the following tools:
            1. **code**: Execute Python code. Use this for math, data analysis (pandas, sklearn), file processing, etc.
               - The code runs in a local environment. You can read files downloaded to 'downloads/'.
            2. **download**: Download a file from a URL.
            3. **submit**: Submit the final answer.

            **Response Format**:
            Return ONLY a valid JSON object. Do not include markdown formatting.
            
            Action 1: Run Code
            {
                "action": "code",
                "code": "import pandas as pd\\n..."
            }

            Action 2: Download File
            {
                "action": "download",
                "url": "https://..."
            }

            Action 3: Submit Answer
            {
                "action": "submit",
                "answer": "the_answer_string",
                "submit_url": "https://..."
            }
            
            Action 4: Give Up / No Info
            {
                "action": "wait",
                "reason": "Need more info"
            }
            """

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Page Content:\n{content[:10000]}"}
            ]
            
            # Append history (previous actions and outputs)
            messages.extend(history)

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"LLM Analysis Failed: {e}")
            return None

    async def solve_and_submit(self, email: str, secret: str, start_url: str, api_token: str = None):
        try:
            await self.start_browser()
            current_url = start_url
            
            # 10-minute timeout for complex tasks
            end_time = asyncio.get_event_loop().time() + 600 

            while current_url and asyncio.get_event_loop().time() < end_time:
                print(f"Visiting: {current_url}")
                await self.page.goto(current_url)
                await self.page.wait_for_load_state("networkidle")
                
                # Extract content
                content = await self.page.evaluate("document.body.innerText")
                links = await self.page.evaluate("""
                    Array.from(document.querySelectorAll('a')).map(a => a.href)
                """)
                content += "\n\nLinks found:\n" + "\n".join(links)

                # ReAct Loop for the current level
                history = []
                max_steps = 5 # Max steps per level to prevent infinite loops
                
                for step in range(max_steps):
                    print(f"--- Step {step + 1} ---")
                    analysis = await self.analyze_with_llm(content, history, api_token)
                    
                    if not analysis:
                        print("LLM failed to analyze.")
                        break

                    action = analysis.get("action")
                    print(f"Action: {action}")

                    if action == "submit":
                        submit_url = analysis.get("submit_url")
                        answer = analysis.get("answer")
                        
                        # Fallback if submit_url is missing in JSON but found in links
                        if not submit_url:
                             submit_url = next((link for link in links if "submit" in link), None)

                        if submit_url:
                            payload = {
                                "email": email,
                                "secret": secret,
                                "url": current_url,
                                "answer": answer
                            }
                            print(f"Submitting to {submit_url}: {payload}")
                            
                            async with aiohttp.ClientSession() as session:
                                async with session.post(submit_url, json=payload) as response:
                                    if response.status == 200:
                                        result = await response.json()
                                        print(f"Submission result: {result}")
                                        if result.get("correct"):
                                            current_url = result.get("url")
                                            if not current_url:
                                                print("Quiz completed!")
                                                return
                                            break # Break ReAct loop, go to next level
                                        else:
                                            print(f"Wrong answer: {result}")
                                            history.append({"role": "assistant", "content": json.dumps(analysis)})
                                            history.append({"role": "user", "content": f"Submission failed. Result: {result}"})
                                    else:
                                        print(f"Submission error: {response.status}")
                                        break
                        else:
                            print("No submit URL found.")
                            break

                    elif action == "code":
                        code = analysis.get("code")
                        print("Executing code...")
                        output = self.executor.execute(code)
                        print(f"Code Output: {output[:500]}...") # Log partial output
                        
                        history.append({"role": "assistant", "content": json.dumps(analysis)})
                        history.append({"role": "user", "content": f"Code Output:\n{output}"})

                    elif action == "download":
                        url = analysis.get("url")
                        print(f"Downloading {url}...")
                        path = self.downloader.download(url)
                        print(f"Downloaded to {path}")
                        
                        history.append({"role": "assistant", "content": json.dumps(analysis)})
                        history.append({"role": "user", "content": f"File downloaded to: {path}"})
                    
                    elif action == "wait":
                        print("LLM requested to wait/give up.")
                        break
                    
                else:
                    print("Max steps reached for this level.")
                    break

        except Exception as e:
            print(f"Error during solving: {e}")
        finally:
            await self.close_browser()
