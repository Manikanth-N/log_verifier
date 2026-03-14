import os
import uuid
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / '.env')
logger = logging.getLogger(__name__)


class AIInsights:
    """GPT-5.2 powered flight analysis insights."""

    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY', '')

    async def analyze(self, diagnostics: Dict[str, Any], user_context: Optional[str] = None) -> Dict[str, Any]:
        """Generate AI-powered insights from diagnostics data."""
        if not self.api_key:
            return {"error": "AI key not configured", "insights": ""}

        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage

            system_message = """You are an expert ArduPilot flight analyst. You analyze drone flight log diagnostics and provide clear, actionable insights.

For beginners: Use simple language, avoid jargon, explain what each issue means practically.
For professionals: Include technical details, reference ArduPilot parameters, suggest specific tuning values.

Structure your response with:
1. **Flight Summary** - Overall assessment
2. **Key Issues** - Most important findings
3. **Recommendations** - Prioritized action items
4. **Technical Details** - For advanced users

Be concise but thorough. Use bullet points for readability."""

            chat = LlmChat(
                api_key=self.api_key,
                session_id=str(uuid.uuid4()),
                system_message=system_message,
            ).with_model("openai", "gpt-5.2")

            # Build analysis prompt
            prompt_parts = ["Analyze this ArduPilot flight log diagnostics:\n"]
            prompt_parts.append(f"Health Score: {diagnostics.get('health_score', 'N/A')}/100")
            prompt_parts.append(f"Critical Issues: {diagnostics.get('critical', 0)}")
            prompt_parts.append(f"Warnings: {diagnostics.get('warnings', 0)}")
            prompt_parts.append(f"Passed Checks: {diagnostics.get('passed', 0)}\n")

            for check in diagnostics.get("checks", []):
                prompt_parts.append(f"[{check['status'].upper()}] {check['name']}: {check['explanation']}")

            if user_context:
                prompt_parts.append(f"\nUser notes: {user_context}")

            prompt_parts.append("\nProvide a comprehensive analysis with recommendations.")

            user_message = UserMessage(text="\n".join(prompt_parts))
            response = await chat.send_message(user_message)

            return {
                "insights": response,
                "model": "gpt-5.2",
            }

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return {
                "error": str(e),
                "insights": "AI analysis is temporarily unavailable. Please check your API key configuration.",
            }
