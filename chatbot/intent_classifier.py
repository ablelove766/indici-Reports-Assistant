"""
Professional Intent Classification System for indici Reports Chatbot.
Implements fast, reliable intent detection with pattern matching and fuzzy logic.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, date

logger = logging.getLogger(__name__)

class IntentType(Enum):
    """Enumeration of all supported intents."""
    PROVIDER_CAPITATION_REPORT = "provider_capitation_report"
    INCOME_PROVIDERS_LIST = "income_providers_list"
    HEALTH_CHECK = "health_check"
    SAMPLE_QUERIES = "sample_queries"
    GREETING = "greeting"
    HELP = "help"
    GOODBYE = "goodbye"
    UNKNOWN = "unknown"

@dataclass
class IntentResult:
    """Result of intent classification."""
    intent: IntentType
    confidence: float
    parameters: Dict[str, Any]
    requires_llm: bool = False
    fallback_reason: Optional[str] = None

@dataclass
class IntentPattern:
    """Pattern definition for intent matching."""
    keywords: List[str]
    required_keywords: List[str]
    negative_keywords: List[str]
    regex_patterns: List[str]
    parameter_extractors: Dict[str, str]

class ProfessionalIntentClassifier:
    """
    Professional-grade intent classifier with pattern matching,
    fuzzy logic, and parameter extraction.
    """
    
    def __init__(self):
        """Initialize the intent classifier with predefined patterns."""
        self.intent_patterns = self._initialize_intent_patterns()
        self.typo_corrections = self._initialize_typo_corrections()
        
    def _initialize_intent_patterns(self) -> Dict[IntentType, IntentPattern]:
        """Initialize intent patterns for classification."""
        return {
            IntentType.PROVIDER_CAPITATION_REPORT: IntentPattern(
                keywords=[
                    "provider", "capitation", "report", "financial", "revenue",
                    "payment", "summary", "data", "monthly", "yearly", "annual",
                    "print", "show", "display", "generate", "get"
                ],
                required_keywords=["provider"],  # Only require "provider" to be more flexible
                negative_keywords=["list", "names", "available", "what", "who"],
                regex_patterns=[
                    r"provider\s+capitation\s+report",
                    r"capitation\s+report",
                    r"provider\s+report",
                    r"financial\s+report",
                    r"revenue\s+report",
                    r"payment\s+report",
                    r"monthly\s+summary",
                    r"yearly\s+summary"
                ],
                parameter_extractors={
                    "provider_name": r"(?:for|provider|dr\.?)\s+([a-zA-Z\s]+?)(?:\s|$|,|\.|!|\?)",
                    "print_report": r"\b(?:print|printing|printable)\b",
                    "monthly": r"\b(?:monthly|month|this\s+month|current\s+month)\b",
                    "yearly": r"\b(?:yearly|annual|year|this\s+year|current\s+year)\b"
                }
            ),
            
            IntentType.INCOME_PROVIDERS_LIST: IntentPattern(
                keywords=[
                    "provider", "list", "names", "available", "show", "all",
                    "income", "providers", "who", "what"
                ],
                required_keywords=["provider"],
                negative_keywords=["capitation", "report", "financial"],
                regex_patterns=[
                    r"provider\s+list",
                    r"income\s+provider",
                    r"available\s+provider",
                    r"show\s+provider",
                    r"what\s+provider"
                ],
                parameter_extractors={}
            ),
            
            IntentType.HEALTH_CHECK: IntentPattern(
                keywords=[
                    "health", "check", "status", "working", "system", "test",
                    "connection", "service", "up", "running", "ok"
                ],
                required_keywords=["health", "check"],
                negative_keywords=[],
                regex_patterns=[
                    r"health\s+check",
                    r"system\s+status",
                    r"is\s+(?:system|service)\s+(?:working|running|up)",
                    r"check\s+(?:system|service|status)"
                ],
                parameter_extractors={}
            ),
            
            IntentType.GREETING: IntentPattern(
                keywords=[
                    "hello", "hi", "hey", "good", "morning", "afternoon",
                    "evening", "greetings", "howdy", "there"
                ],
                required_keywords=["hello", "hi", "hey", "good"],  # At least one greeting word
                negative_keywords=["report", "provider", "capitation"],
                regex_patterns=[
                    r"^(?:hello|hi|hey)(?:\s|!|$)",
                    r"good\s+(?:morning|afternoon|evening)",
                    r"^greetings",
                    r"hello\s+there",
                    r"hi\s+there"
                ],
                parameter_extractors={}
            ),
            
            IntentType.HELP: IntentPattern(
                keywords=[
                    "help", "what", "can", "do", "commands", "options",
                    "available", "features", "capabilities"
                ],
                required_keywords=["help"],
                negative_keywords=[],
                regex_patterns=[
                    r"\bhelp\b",
                    r"what\s+can\s+(?:you|i)\s+do",
                    r"what\s+(?:commands|options|features)",
                    r"show\s+(?:commands|options|help)"
                ],
                parameter_extractors={}
            )
        }
    
    def _initialize_typo_corrections(self) -> Dict[str, str]:
        """Initialize common typo corrections."""
        return {
            # Capitation variations
            'captiation': 'capitation',
            'captation': 'capitation', 
            'capiation': 'capitation',
            'captiation': 'capitation',
            
            # Provider variations
            'providor': 'provider',
            'providr': 'provider',
            'provder': 'provider',
            'provier': 'provider',
            
            # Report variations
            'repot': 'report',
            'reort': 'report',
            'reoprt': 'report',
            
            # Financial variations
            'finacial': 'financial',
            'financal': 'financial',
            'finanical': 'financial',
            
            # Time variations
            'montly': 'monthly',
            'monthyl': 'monthly',
            'yealy': 'yearly',
            'anual': 'annual',
            'sumary': 'summary',
            'summry': 'summary',
            
            # System variations
            'healt': 'health',
            'chek': 'check',
            'staus': 'status',
            'systm': 'system'
        }
    
    def preprocess_message(self, message: str) -> str:
        """Preprocess message by correcting typos and normalizing."""
        # Convert to lowercase
        processed = message.lower().strip()
        
        # Correct common typos
        for typo, correction in self.typo_corrections.items():
            processed = re.sub(r'\b' + re.escape(typo) + r'\b', correction, processed)
        
        # Normalize whitespace
        processed = re.sub(r'\s+', ' ', processed)
        
        return processed
    
    def classify_intent(self, message: str) -> IntentResult:
        """
        Classify user intent using pattern matching and fuzzy logic.
        
        Args:
            message: User input message
            
        Returns:
            IntentResult with classification details
        """
        try:
            # Preprocess message
            processed_message = self.preprocess_message(message)
            
            # Try pattern matching with lower thresholds for better coverage
            best_match = None
            best_confidence = 0.0

            for intent_type, pattern in self.intent_patterns.items():
                result = self._match_pattern(processed_message, intent_type, pattern)
                if result.confidence > best_confidence:
                    best_confidence = result.confidence
                    best_match = result

            # Return best match if confidence is reasonable (lowered threshold)
            if best_match and best_confidence >= 0.3:  # Lowered from 0.5 to 0.3
                logger.info(f"Intent classified: {best_match.intent.value} (confidence: {best_confidence:.2f})")
                return best_match
            
            # Fallback to LLM for complex cases
            logger.info(f"Intent classification uncertain, falling back to LLM")
            return IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                parameters={},
                requires_llm=True,
                fallback_reason="No clear intent pattern matched"
            )
            
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                parameters={},
                requires_llm=True,
                fallback_reason=f"Classification error: {str(e)}"
            )
    
    def _match_pattern(self, message: str, intent_type: IntentType, pattern: IntentPattern) -> IntentResult:
        """Match message against a specific intent pattern."""
        confidence = 0.0
        parameters = {}
        
        # Check for negative keywords (disqualifiers)
        for neg_keyword in pattern.negative_keywords:
            if neg_keyword in message:
                return IntentResult(intent_type, 0.0, {})
        
        # Check required keywords (more flexible - only need one match)
        required_score = 0
        if pattern.required_keywords:
            for req_keyword in pattern.required_keywords:
                if req_keyword in message:
                    required_score += 1

            # For greetings and help, only need one match; for others, be more flexible
            if intent_type in [IntentType.GREETING, IntentType.HELP]:
                if required_score == 0:
                    return IntentResult(intent_type, 0.0, {})
                confidence += min(required_score / len(pattern.required_keywords), 1.0) * 0.6
            else:
                # For other intents, give partial credit
                confidence += (required_score / len(pattern.required_keywords)) * 0.4
        
        # Check regex patterns
        regex_score = 0
        for regex_pattern in pattern.regex_patterns:
            if re.search(regex_pattern, message, re.IGNORECASE):
                regex_score += 1
        
        if regex_score > 0:
            confidence += min(regex_score / len(pattern.regex_patterns), 1.0) * 0.4
        
        # Check general keywords
        keyword_score = 0
        for keyword in pattern.keywords:
            if keyword in message:
                keyword_score += 1
        
        if keyword_score > 0:
            confidence += min(keyword_score / len(pattern.keywords), 1.0) * 0.3
        
        # Extract parameters
        for param_name, param_pattern in pattern.parameter_extractors.items():
            if param_name == "print_report":
                if re.search(param_pattern, message, re.IGNORECASE):
                    parameters["print_report"] = True
            elif param_name == "monthly":
                if re.search(param_pattern, message, re.IGNORECASE):
                    parameters["date_from"] = self._get_current_month_start()
                    parameters["date_to"] = self._get_current_date()
            elif param_name == "yearly":
                if re.search(param_pattern, message, re.IGNORECASE):
                    parameters["date_from"] = self._get_current_year_start()
                    parameters["date_to"] = self._get_current_date()
            elif param_name == "provider_name":
                match = re.search(param_pattern, message, re.IGNORECASE)
                if match:
                    provider_name = match.group(1).strip().title()
                    # Clean up common false positives
                    if provider_name.lower() not in ["capitation", "report", "provider", "monthly", "yearly"]:
                        parameters["provider_name"] = provider_name
        
        return IntentResult(intent_type, min(confidence, 1.0), parameters)
    
    def _get_current_month_start(self) -> str:
        """Get first day of current month."""
        today = date.today()
        return today.replace(day=1).strftime("%Y-%m-%d")
    
    def _get_current_year_start(self) -> str:
        """Get first day of current year."""
        today = date.today()
        return today.replace(month=1, day=1).strftime("%Y-%m-%d")
    
    def _get_current_date(self) -> str:
        """Get current date."""
        return date.today().strftime("%Y-%m-%d")
