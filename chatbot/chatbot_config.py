"""
Simple Configuration Manager for indici Reports Chatbot.
Handles Intent vs LLM approach based on true/false settings.
"""

import json
import logging
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SidebarItem:
    """Sidebar menu item configuration."""
    id: str
    label: str
    query: str
    icon: str

class SimpleConfigManager:
    """
    Simple configuration manager that switches between
    Intent approach and LLM approach based on config.json settings.
    """
    
    def __init__(self, config_path: str = "chatbot_config.json"):
        """Initialize the configuration manager."""
        self.config_path = config_path
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            self.config = self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config = self._get_default_config()
    
    def use_intent_approach(self) -> bool:
        """Check if intent approach should be used."""
        return self.config.get("model_selection", {}).get("use_intent", True)

    def use_groq(self) -> bool:
        """Check if Groq model should be used."""
        return self.config.get("model_selection", {}).get("use_groq", False)

    def use_qwen(self) -> bool:
        """Check if QWEN model should be used."""
        return self.config.get("model_selection", {}).get("use_qwen", False)

    def get_fallback_order(self) -> List[str]:
        """Get fallback order for model selection."""
        return self.config.get("model_selection", {}).get("fallback_order", ["intent", "groq", "qwen"])
    
    def get_sidebar_items(self) -> List[SidebarItem]:
        """Get sidebar menu items."""
        sidebar_config = self.config.get("sidebar_configuration", {})
        items = []
        
        enabled_sections = sidebar_config.get("enabled_sections", [])
        
        for section in enabled_sections:
            section_config = sidebar_config.get(section, {})
            section_items = section_config.get("items", [])
            
            for item_config in section_items:
                items.append(SidebarItem(
                    id=item_config.get("id", ""),
                    label=item_config.get("label", ""),
                    query=item_config.get("query", ""),
                    icon=item_config.get("icon", "📄")
                ))
        
        return items
    
    def get_sidebar_configuration(self) -> Dict[str, Any]:
        """Get sidebar configuration for frontend with collapsible menu support."""
        sidebar_config = self.config.get("sidebar_configuration", {})
        enabled_sections = sidebar_config.get("enabled_sections", [])

        sections = []
        for section in enabled_sections:
            section_config = sidebar_config.get(section, {})

            if section_config:
                sections.append({
                    "id": section,
                    "title": section_config.get("title", "Menu"),
                    "collapsible": section_config.get("collapsible", False),
                    "expanded": section_config.get("expanded", True),
                    "icon": section_config.get("icon", "📄"),
                    "toggle_style": section_config.get("toggle_style", "arrow"),
                    "items": [
                        {
                            "id": item.get("id", ""),
                            "label": item.get("label", ""),
                            "query": item.get("query", ""),
                            "icon": item.get("icon", "📄")
                        }
                        for item in section_config.get("items", [])
                    ]
                })

        return {
            "sections": sections,
            "title": "Provider Capitation Queries"
        }
    
    def get_current_approach(self) -> str:
        """Get current processing approach."""
        use_intent = self.use_intent_approach()
        use_groq = self.use_groq()
        use_qwen = self.use_qwen()

        if use_qwen and not use_groq and not use_intent:
            return "qwen_only"
        elif use_groq and not use_qwen and not use_intent:
            return "groq_only"
        elif use_intent and not use_groq and not use_qwen:
            return "intent_only"
        elif use_qwen or use_groq or use_intent:
            return "multiple_enabled"
        else:
            return "none_enabled"
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "model_selection": {
                "use_groq": False,
                "use_intent": True,
                "use_qwen": False,
                "fallback_order": ["intent", "groq", "qwen"]
            },
            "sidebar_configuration": {
                "enabled_sections": ["provider_capitation_queries"],
                "provider_capitation_queries": {
                    "title": "Provider Capitation Queries",
                    "items": [
                        {
                            "id": "monthly_report",
                            "label": "Generate Monthly Report",
                            "query": "generate monthly provider capitation report",
                            "icon": "📊"
                        },
                        {
                            "id": "yearly_summary", 
                            "label": "Yearly Summary",
                            "query": "generate yearly provider capitation summary",
                            "icon": "📈"
                        },
                        {
                            "id": "print_report",
                            "label": "Print Provider Report",
                            "query": "print provider capitation report",
                            "icon": "🖨️"
                        },
                        {
                            "id": "provider_list",
                            "label": "Provider List For Capitation",
                            "query": "show all providers for provider capitation report",
                            "icon": "👥"
                        }
                    ]
                }
            }
        }
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration."""
        return {
            "current_approach": self.get_current_approach(),
            "use_intent_approach": self.use_intent_approach(),
            "use_groq": self.use_groq(),
            "use_qwen": self.use_qwen(),
            "fallback_order": self.get_fallback_order(),
            "sidebar_items_count": len(self.get_sidebar_items())
        }
