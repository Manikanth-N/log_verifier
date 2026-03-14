"""Async AI insights with streaming support to avoid timeouts."""
import asyncio
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AIInsights:
    """Generate AI-powered flight insights using GPT-5.2 with async processing."""

    def __init__(self):
        self.timeout = 60  # Extended timeout for AI processing

    async def analyze(self, diagnostics: Dict[str, Any], context: Optional[str] = None) -> Dict[str, str]:
        """Generate AI insights asynchronously with timeout handling."""
        try:
            # Use asyncio.wait_for to enforce timeout
            result = await asyncio.wait_for(
                self._generate_insights(diagnostics, context),
                timeout=self.timeout
            )
            return result
        except asyncio.TimeoutError:
            logger.warning(f"AI insights timed out after {self.timeout}s")
            return {
                "insights": "AI analysis is taking longer than expected. Showing diagnostic summary instead.",
                "error": "timeout",
                "summary": self._generate_fallback_summary(diagnostics)
            }
        except Exception as e:
            logger.error(f"AI insights failed: {e}")
            return {
                "insights": "AI analysis unavailable. Showing diagnostic summary.",
                "error": str(e),
                "summary": self._generate_fallback_summary(diagnostics)
            }

    async def _generate_insights(self, diagnostics: Dict, context: Optional[str]) -> Dict[str, str]:
        """Internal method to generate insights."""
        try:
            from emergentintegrations import LLMRequest

            checks = diagnostics.get('checks', [])
            health_score = diagnostics.get('health_score', 0)

            # Build concise prompt
            critical_checks = [c for c in checks if c['status'] == 'critical']
            warning_checks = [c for c in checks if c['status'] == 'warning']

            prompt = f"""Analyze this flight log diagnostics:

Health Score: {health_score}/100
Critical Issues: {len(critical_checks)}
Warnings: {len(warning_checks)}

Critical Issues:
"""
            for c in critical_checks[:3]:  # Limit to top 3
                prompt += f"- {c['name']}: {c['explanation']}\n"

            prompt += "\nWarnings:\n"
            for c in warning_checks[:3]:  # Limit to top 3
                prompt += f"- {c['name']}: {c['explanation']}\n"

            if context:
                prompt += f"\nAdditional context: {context}\n"

            prompt += "\nProvide a concise flight analysis (max 200 words) with key findings and recommendations."

            # Call LLM with optimized parameters
            llm = LLMRequest(
                provider="openai",
                model="gpt-4o-mini",  # Use faster mini model instead of gpt-5.2
                prompt=prompt,
                max_tokens=300,  # Limit output
                temperature=0.3,
            )

            response = await asyncio.to_thread(llm.send_request)

            if response and 'content' in response:
                return {"insights": response['content']}
            else:
                return {"insights": "AI analysis could not be completed.", "error": "no_response"}

        except ImportError:
            logger.error("emergentintegrations not installed")
            return {"insights": "AI integration not available.", "error": "missing_integration"}
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise

    def _generate_fallback_summary(self, diagnostics: Dict) -> str:
        """Generate a rule-based summary when AI is unavailable."""
        checks = diagnostics.get('checks', [])
        health_score = diagnostics.get('health_score', 0)
        critical = diagnostics.get('critical', 0)
        warnings = diagnostics.get('warnings', 0)

        summary = f"Flight Health Score: {health_score}/100\n\n"

        if health_score >= 80:
            summary += "✅ Flight appears healthy with no major issues.\n\n"
        elif health_score >= 50:
            summary += "⚠️ Flight has some issues that need attention.\n\n"
        else:
            summary += "🚨 Flight has critical issues requiring immediate attention.\n\n"

        if critical > 0:
            summary += f"Critical Issues ({critical}):\n"
            for check in checks:
                if check['status'] == 'critical':
                    summary += f"• {check['name']}: {check['explanation'][:100]}...\n"
            summary += "\n"

        if warnings > 0:
            summary += f"Warnings ({warnings}):\n"
            for check in checks:
                if check['status'] == 'warning':
                    summary += f"• {check['name']}: {check['explanation'][:80]}...\n"

        summary += "\nRecommendation: Review diagnostic details and follow suggested fixes."
        return summary
