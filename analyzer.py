import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import google.generativeai as genai

from hf_scraper import SpaceInfo, fetch_recent_spaces
from config import settings

logger = logging.getLogger(__name__)


@dataclass
class AnalysisReport:
    space_name: str
    space_url: str
    likes: int
    created_at: str
    description: str
    innovation_score: float
    likes_speed_score: float
    ease_of_execution_score: float
    overall_score: float
    idea_summary: str
    why_it_stands_out: str
    development_suggestions: str


def _initialize_gemini() -> None:
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables.")
    genai.configure(api_key=api_key)


def _calculate_like_speed(likes: int, created_at: Optional[str]) -> float:
    if created_at is None:
        return min(likes / 10.0, 10.0)
    try:
        if isinstance(created_at, datetime):
            created_dt = created_at
        else:
            created_str = str(created_at).replace("Z", "+00:00")
            created_dt = datetime.fromisoformat(created_str)
        now_dt = datetime.now(created_dt.tzinfo) if created_dt.tzinfo else datetime.now()
        hours_since = (now_dt - created_dt).total_seconds() / 3600.0
        if hours_since < 1:
            hours_since = 1.0
        score = (likes / hours_since) * 10.0
        return min(score, 10.0)
    except (ValueError, TypeError, OverflowError):
        return min(likes / 10.0, 10.0)


def _build_prompt(spaces: List[SpaceInfo]) -> str:
    spaces_text_lines: List[str] = []
    for i, space in enumerate(spaces, start=1):
        created_info = str(space.created_at) if space.created_at else "غير معروف"
        spaces_text_lines.append(
            f"المشروع {i}:\n"
            f"- الاسم: {space.name}\n"
            f"- الرابط: {space.url}\n"
            f"- عدد الإعجابات: {space.likes}\n"
            f"- تاريخ الإنشاء: {created_info}\n"
            f"- الوصف: {space.description or 'لا يوجد وصف'}"
        )
    spaces_text = "\n".join(spaces_text_lines)

    return (
        "أنت محلل ذكي لمشاريع التكنولوجيا والذكاء الاصطناعي. لديك قائمة بمشاريع حديثة على Hugging Face Spaces. "
        "قم بتحليل كل مشروع وتقييمه وفق المعايير الثلاثة التالية:\n\n"
        "1. **ابتكار الفكرة** (0-10): مدى تميز الفكرة وحداثتها وعدم تكرارها.\n"
        "2. **سرعة جمع الإعجابات** (0-10): مدى سرعة نمو المشروع بناءً على عدد الإعجابات مقارنة بزمن إنشائه.\n"
        "3. **سهولة إعادة التنفيذ** (0-10): مدى إمكانية بناء نسخة مشابهة أو محسّنة بسهولة باستخدام أدوات متاحة.\n\n"
        "لكل مشروع، أعد النتائج بصيغة JSON صالحة تحتوي على مصفوفة من الكائنات بنفس ترتيب المشاريع المذكورة أدناه. "
        "كل كائن يحتوي على:\n"
        "- innovation_score: رقم عشري بين 0 و 10\n"
        "- likes_speed_score: رقم عشري بين 0 و 10\n"
        "- ease_of_execution_score: رقم عشري بين 0 و 10\n"
        "- overall_score: المتوسط الحسابي للدرجات الثلاث (رقم عشري بين 0 و 10)\n"
        "- idea_summary: ملخص مختصر للفكرة بالعربية (جملة أو جملتان)\n"
        "- why_it_stands_out: أبرز الأسباب التي تجعل هذه الفكرة تستحق الاهتمام (3-5 نقاط)\n"
        "- development_suggestions: مقترحات عملية لتطوير المشروع أو إعادة تنفيذه بشكل أفضل (3-5 نقاط)\n\n"
        f"قائمة المشاريع:\n{spaces_text}\n\n"
        "أعد النتائج فقط بصيغة JSON صالحة بدون أي نص إضافي خارج JSON."
    )


def _parse_gemini_response(response_text: str) -> List[dict]:
    try:
        json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            parsed = json.loads(json_str)
            if isinstance(parsed, list):
                return parsed
    except (json.JSONDecodeError, AttributeError) as e:
        logger.warning(f"Failed to parse JSON array from Gemini response: {e}")

    try:
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            parsed = json.loads(json_str)
            if isinstance(parsed, dict) and "results" in parsed:
                results = parsed["results"]
                if isinstance(results, list):
                    return results
            elif isinstance(parsed, dict):
                return [parsed]
    except (json.JSONDecodeError, AttributeError) as e:
        logger.warning(f"Failed to parse JSON object from Gemini response: {e}")

    logger.warning("Could not parse any valid JSON from Gemini response.")
    return []


def _normalize_analysis(analysis: dict, default_scores: tuple = (0.0, 0.0, 0.0)) -> dict:
    if not isinstance(analysis, dict):
        analysis = {}
    return {
        "innovation_score": float(analysis.get("innovation_score", default_scores[0])),
        "likes_speed_score": float(analysis.get("likes_speed_score", default_scores[1])),
        "ease_of_execution_score": float(analysis.get("ease_of_execution_score", default_scores[2])),
        "overall_score": float(analysis.get("overall_score", 0.0)),
        "idea_summary": str(analysis.get("idea_summary", "")),
        "why_it_stands_out": str(analysis.get("why_it_stands_out", "")),
        "development_suggestions": str(analysis.get("development_suggestions", "")),
    }


def analyze_spaces() -> List[AnalysisReport]:
    spaces: List[SpaceInfo] = fetch_recent_spaces()
    if not spaces:
        logger.info("No recent spaces found to analyze.")
        return []

    logger.info(f"Fetched {len(spaces)} spaces for analysis.")

    try:
        _initialize_gemini()
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt: str = _build_prompt(spaces)
        response = model.generate_content(prompt, generation_config={
            "temperature": 0.3,
            "max_output_tokens": 8192,
        })
        raw_analyses: List[dict] = _parse_gemini_response(response.text)
    except Exception as exc:
        logger.error(f"Error calling Gemini API: {exc}")
        return []

    if not raw_analyses:
        logger.warning("Gemini returned no valid analysis results. Using fallback scores.")
        raw_analyses = [
            {
                "innovation_score": 0.0,
                "likes_speed_score": 0.0,
                "ease_of_execution_score": 0.0,
                "overall_score": 0.0,
                "idea_summary": "لم تتمكن التحليلات التلقائية من تقييم هذا المشروع.",
                "why_it_stands_out": "لا توجد بيانات تحليل متاحة.",
                "development_suggestions": "يرجى مراجعة المشروع يدوياً.",
            }
            for _ in spaces
        ]

    reports: List[AnalysisReport] = []
    for i, space in enumerate(spaces):
        if i < len(raw_analyses):
            analysis = _normalize_analysis(raw_analyses[i])
        else:
            analysis = _normalize_analysis({})

        like_speed: float = _calculate_like_speed(space.likes, space.created_at)
        overall: float = round(
            (analysis["innovation_score"] + analysis["likes_speed_score"] + analysis["ease_of_execution_score"]) / 3.0,
            2,
        )

        report = AnalysisReport(
            space_name=space.name,
            space_url=space.url,
            likes=space.likes,
            created_at=str(space.created_at) if space.created_at else "غير معروف",
            description=space.description or "",
            innovation_score=analysis["innovation_score"],
            likes_speed_score=round(like_speed, 2),
            ease_of_execution_score=analysis["ease_of_execution_score"],
            overall_score=overall,
            idea_summary=analysis["idea_summary"],
            why_it_stands_out=analysis["why_it_stands_out"],
            development_suggestions=analysis["development_suggestions"],
        )
        reports.append(report)
        logger.info(
            f"Analyzed '{space.name}' - Innovation: {analysis['innovation_score']}, "
            f"Likes Speed: {round(like_speed, 2)}, Ease: {analysis['ease_of_execution_score']}, "
            f"Overall: {overall}"
        )

    reports.sort(key=lambda r: r.overall_score, reverse=True)
    logger.info(f"Analysis complete. {len(reports)} reports generated and sorted by overall score.")
    return reports
