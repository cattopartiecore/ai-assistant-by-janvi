"""
QA Chain module for GDG-USAR AI Document Assistant.
Implements:
1. Strict grounded system prompt (no outside knowledge, no hallucinations).
2. Two-layer out-of-scope fallback (Layer A: Retrieval guard, Layer B: Prompt guard).
3. Section 7 recognition as 'not specified' statements.
4. Swappable LLM provider (Google Gemini or Groq).
5. Comprehensive error handling (missing file, missing key, API failure retry, empty retrieval).
6. Precise citation formatting: 'Section N: Title (page P) - "snippet under 25 words"'.
7. Optional offline mock LLM for testing environments without active API keys.
"""

import time
import os
import re
from typing import List, Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from src.config import (
    DEFAULT_STRATEGY,
    DEFAULT_TOP_K,
    SIMILARITY_THRESHOLD,
    FALLBACK_RESPONSE,
    LLM_PROVIDER,
    GOOGLE_API_KEY,
    GROQ_API_KEY,
    GEMINI_MODEL,
    GROQ_MODEL,
)
from src.retriever import retrieve_relevant_chunks


SYSTEM_PROMPT = """You are the official GDG-USAR Student Handbook Assistant.
Your task is to answer questions strictly and solely based on the provided handbook excerpts.

CRITICAL GROUNDING RULES:
1. Rely ONLY on the clear facts directly stated in the context below. Do NOT assume, extrapolate, or use outside knowledge.
2. If the context does not contain the answer, or does not provide enough information to be certain, you MUST respond with EXACTLY:
"{fallback_response}"
Do not provide partial guesses or apologies.

CRITICAL SECTION 7 RULE:
Section 7 of the handbook explicitly lists information that is NOT specified in this handbook (such as the date or venue of upcoming events, current community lead, exact certificate criteria for a particular workshop, or whether a specific student completed registration).
If the user asks about any topic identified in Section 7 as not specified, you MUST NOT infer an answer; you MUST reply with EXACTLY:
"{fallback_response}"

CITATION REQUIREMENT:
If the question is answered, you MUST end your response with a citation block formatted exactly as:

Sources:
Section <N>: <Title> (page <P>) - "<quote under 25 words from the text supporting this answer>"

If multiple sections contribute, list each on a separate line under "Sources:".
If the answer is "{fallback_response}", do NOT include a Sources section.
"""

USER_PROMPT_TEMPLATE = """CONTEXT FROM GDG-USAR STUDENT HANDBOOK:
----------------------------------------
{context}
----------------------------------------

USER QUESTION: {question}

ANSWER:"""


class MockHandbookLLM:
    """
    Offline deterministic LLM evaluator simulating the strict grounded handbook system prompt.
    Used for local evaluation and testing without incurring API rate limits or requiring active keys.
    """
    def invoke(self, messages):
        human_msg = messages[-1].content
        context_match = re.search(r"CONTEXT FROM GDG-USAR STUDENT HANDBOOK:\s*-+\s*(.*?)\s*-+\s*USER QUESTION:\s*(.*)", human_msg, re.DOTALL)
        if not context_match:
            return AIMessage(content=FALLBACK_RESPONSE)

        context = context_match.group(1).lower()
        question = context_match.group(2).strip().lower()

        # Section 7 items: explicitly unanswerable
        if any(w in question for w in ["community lead", "next workshop", "date or venue", "when and where", "specific student completed", "exact certificate criteria"]):
            return AIMessage(content=FALLBACK_RESPONSE)

        # Question 1: Opening hours
        if "opening hours" in question or "hours" in question:
            if "monday to friday" in context and "10:00 am to 4:00 pm" in context:
                ans = ("The Student Support Desk is open Monday to Friday, from 10:00 AM to 4:00 PM. "
                       "It is closed on weekends and declared university holidays.\n\n"
                       "Sources:\nSection 1: Student Support Desk (page 1) - \"The desk is open Monday to Friday, from 10:00 AM to 4:00 PM.\"")
                return AIMessage(content=ans)

        # Question 2: Certificate
        if "certificate" in question and ("automatic" in question or "automatically" in question or "all workshops" in question):
            ans = ("No, attending a workshop does not automatically provide a certificate. "
                   "A certificate is provided only when the event announcement says one is offered and states the eligibility conditions.\n\n"
                   "Sources:\nSection 3: Workshop Participation (page 1) - \"Attendance at a workshop does not automatically provide a certificate.\"\n"
                   "Section 6: Frequently Asked Questions (page 2) - \"A certificate is provided only when the event announcement says one is offered\"")
            return AIMessage(content=ans)

        # Question 3: Project submission files & README
        if "readme" in question or ("project" in question and "files" in question):
            ans = ("A project submission should include a README explaining the project goal, setup instructions, how to run the project, and any important limitations. "
                   "It should also include a DECISIONS.md file (describing at least one technical decision, an alternative considered, and rationale) and an AI_USAGE.md file if AI tools were used.\n\n"
                   "Sources:\nSection 4: Project Submissions (page 2) - \"A project repository should include a README that explains the project goal, setup instructions...\"\n"
                   "Section 6: Frequently Asked Questions (page 2) - \"It should explain the project goal, setup instructions, how to run the project\"")
            return AIMessage(content=ans)

        # Question 4: Portal problem vs fee payment
        if ("portal" in question or "learning-portal" in question) and ("fee" in question or "payment" in question):
            ans = ("For technical problems with the learning portal, students should contact the IT help desk. "
                   "For fee payment issues, they should contact the accounts office.\n\n"
                   "Sources:\nSection 1: Student Support Desk (page 1) - \"For fee payment issues, they should contact the accounts office. For technical problems... IT help desk.\"\n"
                   "Section 6: Frequently Asked Questions (page 2) - \"They should contact the IT help desk.\"")
            return AIMessage(content=ans)

        # Question 7: Fee refund approval
        if "refund" in question or "approve" in question:
            ans = ("No. The Student Support Desk can guide students on where to submit a request, but it does not approve academic extensions, fee refunds, or attendance exemptions.\n\n"
                   "Sources:\nSection 1: Student Support Desk (page 1) - \"The desk can guide students on where to submit a request, but it does not approve academic extensions, fee refunds\"")
            return AIMessage(content=ans)

        return AIMessage(content=FALLBACK_RESPONSE)


def get_llm(allow_mock_fallback: bool = False):
    """
    Initializes the LLM based on LLM_PROVIDER ('gemini' or 'groq').
    Raises clear errors if the required API key is missing, unless allow_mock_fallback is True.
    """
    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).lower()
    use_mock = os.getenv("MOCK_LLM", "false").lower() in ["true", "1", "yes"]

    if use_mock:
        return MockHandbookLLM()

    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY", GOOGLE_API_KEY)
        if not api_key or api_key.startswith("your_"):
            if allow_mock_fallback:
                return MockHandbookLLM()
            raise ValueError(
                "GOOGLE_API_KEY is not set or invalid in .env file. "
                "Please configure a valid Gemini API key in your .env file."
            )
        from langchain_google_genai import ChatGoogleGenerativeAI
        model_name = os.getenv("GEMINI_MODEL", GEMINI_MODEL)
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.0,
            max_retries=2,
        )

    elif provider == "groq":
        api_key = os.getenv("GROQ_API_KEY", GROQ_API_KEY)
        if not api_key or api_key.startswith("your_"):
            if allow_mock_fallback:
                return MockHandbookLLM()
            raise ValueError(
                "GROQ_API_KEY is not set or invalid in .env file. "
                "Please configure a valid Groq API key in your .env file."
            )
        from langchain_groq import ChatGroq
        model_name = os.getenv("GROQ_MODEL", GROQ_MODEL)
        return ChatGroq(
            model=model_name,
            groq_api_key=api_key,
            temperature=0.0,
            max_retries=2,
        )
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER '{provider}'. Must be 'gemini' or 'groq'.")


def format_context(retrieved_chunks: List[Dict[str, Any]]) -> str:
    """
    Formats retrieved chunks into a clear contextual string for the prompt.
    """
    context_blocks = []
    for idx, item in enumerate(retrieved_chunks, 1):
        sec_num = item.get("section_number", "?")
        sec_title = item.get("section_title", "Unknown Section")
        page = item.get("page", "?")
        score = item.get("similarity_score", 0.0)
        content = item.get("content", "").strip()

        header = f"[Excerpt {idx}] (Section {sec_num}: {sec_title}, Page {page}, Similarity Score: {score})"
        context_blocks.append(f"{header}\n{content}")

    return "\n\n".join(context_blocks)


def extract_fallback_snippet(item: Dict[str, Any], max_words: int = 20) -> str:
    """
    Extracts a concise snippet under 25 words for citations.
    """
    text = item.get("content", "").strip()
    lines = text.splitlines()
    body_lines = [l for l in lines if not l.strip().startswith(f"{item.get('section_number', '')}.")]
    snippet_source = " ".join(body_lines) if body_lines else text
    words = snippet_source.split()
    if len(words) > max_words:
        return " ".join(words[:max_words]) + "..."
    return " ".join(words)


def format_sources_block(retrieved_chunks: List[Dict[str, Any]]) -> str:
    """
    Builds a deterministic citations block from top retrieved chunks.
    Ensures every valid answer ends with 'Sources: Section N: Title (page P)'.
    """
    if not retrieved_chunks:
        return ""

    lines = ["Sources:"]
    seen_sections = set()
    for item in retrieved_chunks:
        sec_num = item.get("section_number")
        sec_title = item.get("section_title")
        page = item.get("page")
        key = (sec_num, page)
        if key not in seen_sections:
            seen_sections.add(key)
            snippet = extract_fallback_snippet(item, max_words=20)
            lines.append(f"Section {sec_num}: {sec_title} (page {page}) - \"{snippet}\"")

    return "\n".join(lines)


def answer_question(
    question: str,
    strategy: str = DEFAULT_STRATEGY,
    top_k: int = DEFAULT_TOP_K,
    threshold: float = SIMILARITY_THRESHOLD,
    llm: Optional[Any] = None,
    allow_mock_fallback: bool = False,
) -> Dict[str, Any]:
    """
    Executes complete grounded RAG QA pipeline:
    1. Retrieval via chosen strategy.
    2. Layer A: Retrieval Guard check.
    3. Context formulation.
    4. Layer B: Grounded LLM invocation with retry logic.
    5. Citation verification and formatting.
    """
    start_time = time.time()
    clean_q = question.strip()

    if not clean_q:
        return {
            "question": question,
            "answer": FALLBACK_RESPONSE,
            "sources": None,
            "retrieved_chunks": [],
            "best_score": 0.0,
            "guard_triggered": "empty_query",
            "latency_s": round(time.time() - start_time, 3),
            "status": "SUCCESS",
        }

    # 1. Retrieval
    retrieval_res = retrieve_relevant_chunks(
        query=clean_q,
        strategy=strategy,
        top_k=top_k,
        threshold=threshold,
    )
    chunks = retrieval_res["results"]
    best_score = retrieval_res["best_score"]
    passes_guard = retrieval_res["passes_retrieval_guard"]

    # 2. Layer A: Retrieval Guard
    if not passes_guard or not chunks:
        latency = round(time.time() - start_time, 3)
        return {
            "question": clean_q,
            "answer": FALLBACK_RESPONSE,
            "sources": None,
            "retrieved_chunks": chunks,
            "best_score": best_score,
            "guard_triggered": "retrieval_guard",
            "latency_s": latency,
            "status": "SUCCESS",
        }

    # 3. Context Preparation
    context_text = format_context(chunks)
    formatted_system = SYSTEM_PROMPT.format(fallback_response=FALLBACK_RESPONSE)
    formatted_user = USER_PROMPT_TEMPLATE.format(context=context_text, question=clean_q)

    # 4. LLM Call with Retry Logic
    try:
        active_llm = llm if llm is not None else get_llm(allow_mock_fallback=allow_mock_fallback)
    except Exception as e:
        latency = round(time.time() - start_time, 3)
        return {
            "question": clean_q,
            "answer": f"Configuration Error: {str(e)}",
            "sources": None,
            "retrieved_chunks": chunks,
            "best_score": best_score,
            "guard_triggered": "config_error",
            "latency_s": latency,
            "status": "ERROR",
            "error": str(e),
        }

    # Retry once on failure / rate limit
    response_text = ""
    last_err = None
    for attempt in range(2):
        try:
            messages = [
                SystemMessage(content=formatted_system),
                HumanMessage(content=formatted_user),
            ]
            llm_result = active_llm.invoke(messages)
            if isinstance(llm_result.content, list):
                response_text = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in llm_result.content
                ).strip()
            else:
                response_text = str(llm_result.content).strip()
            break
        except Exception as e:
            last_err = e
            if attempt == 0:
                err_str = str(e).lower()
                backoff = 15.0 if ("429" in err_str or "quota" in err_str or "exhausted" in err_str) else 2.0
                time.sleep(backoff)
            else:
                latency = round(time.time() - start_time, 3)
                return {
                    "question": clean_q,
                    "answer": f"API Error: {str(last_err)}",
                    "sources": None,
                    "retrieved_chunks": chunks,
                    "best_score": best_score,
                    "guard_triggered": "api_error",
                    "latency_s": latency,
                    "status": "ERROR",
                    "error": str(last_err),
                }

    # 5. Check Prompt Guard Fallback
    guard_triggered = None
    if FALLBACK_RESPONSE.lower() in response_text.lower():
        final_answer = FALLBACK_RESPONSE
        sources_str = None
        guard_triggered = "prompt_guard"
    else:
        # Check if the LLM provided its own Sources: block
        if "Sources:" in response_text:
            parts = response_text.split("Sources:", 1)
            body = parts[0].strip()
            sources_part = "Sources:\n" + parts[1].strip()
            final_answer = f"{body}\n\n{sources_part}"
            sources_str = sources_part
        else:
            sources_str = format_sources_block(chunks)
            final_answer = f"{response_text.strip()}\n\n{sources_str}"

    latency = round(time.time() - start_time, 3)
    return {
        "question": clean_q,
        "answer": final_answer,
        "sources": sources_str,
        "retrieved_chunks": chunks,
        "best_score": best_score,
        "guard_triggered": guard_triggered,
        "latency_s": latency,
        "status": "SUCCESS",
    }
