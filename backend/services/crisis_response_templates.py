"""
Crisis Response Templates Service
Comprehensive crisis response templates with appropriate resources

This service provides age-appropriate crisis response templates for different
crisis categories detected by the safety filter. All templates are designed
for kids ages 8-14 with appropriate language and resource referrals.
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger("chatbot.crisis_response_templates")


class CrisisResponseTemplates:
    """
    Crisis Response Templates - Comprehensive crisis response management

    Features:
    - Category-specific templates (suicide, self-harm, abuse types)
    - Age-appropriate language for kids 8-14
    - Appropriate resource referrals for each crisis type
    - Personalization options (user name, context)
    - Consistent messaging and tone

    Crisis Categories:
    - suicide: Suicidal ideation or intent
    - self_harm: Self-harm behaviors or urges
    - abuse_physical: Physical abuse or violence
    - abuse_emotional: Emotional or psychological abuse
    - abuse_sexual: Sexual abuse or inappropriate contact
    """

    def __init__(self):
        """Initialize CrisisResponseTemplates"""

        # Core message components
        self.concern_openings = {
            "suicide": "I'm really worried about what you just said, and I want to help.",
            "self_harm": "I'm really concerned about what you shared with me.",
            "abuse_physical": "I'm really worried about what you just told me.",
            "abuse_emotional": "I'm really concerned about what you described.",
            "abuse_sexual": "I'm very concerned about what you just told me.",
        }

        self.validation_messages = {
            "suicide": "What you're feeling is really important, but I'm not able to help with something this serious.",
            "self_harm": "Your feelings matter, but I'm not equipped to help with something like this.",
            "abuse_physical": "What you described sounds serious, and I want to make sure you're safe.",
            "abuse_emotional": "What you're experiencing is not okay, and you deserve support.",
            "abuse_sexual": "What you described is very serious, and it's not your fault.",
        }

        # Crisis resources by category
        self.crisis_resources = {
            "suicide": {
                "primary": {
                    "name": "National Suicide Prevention Lifeline",
                    "contact": "988 (call or text)",
                    "description": "24/7 confidential support",
                },
                "secondary": {
                    "name": "Crisis Text Line",
                    "contact": "Text HOME to 741741",
                    "description": "Free, 24/7 crisis support via text",
                },
            },
            "self_harm": {
                "primary": {
                    "name": "Crisis Text Line",
                    "contact": "Text HOME to 741741",
                    "description": "Free, 24/7 crisis support via text",
                },
                "secondary": {
                    "name": "National Suicide Prevention Lifeline",
                    "contact": "988 (call or text)",
                    "description": "24/7 confidential support",
                },
            },
            "abuse_physical": {
                "primary": {
                    "name": "Childhelp National Child Abuse Hotline",
                    "contact": "1-800-422-4453",
                    "description": "24/7 professional crisis counselors",
                },
                "secondary": {
                    "name": "Emergency Services",
                    "contact": "911",
                    "description": "If you're in immediate danger",
                },
            },
            "abuse_emotional": {
                "primary": {
                    "name": "Childhelp National Child Abuse Hotline",
                    "contact": "1-800-422-4453",
                    "description": "24/7 professional crisis counselors",
                },
                "secondary": {
                    "name": "Crisis Text Line",
                    "contact": "Text HOME to 741741",
                    "description": "Free, 24/7 support via text",
                },
            },
            "abuse_sexual": {
                "primary": {
                    "name": "Childhelp National Child Abuse Hotline",
                    "contact": "1-800-422-4453",
                    "description": "24/7 professional crisis counselors",
                },
                "secondary": {
                    "name": "RAINN National Sexual Assault Hotline",
                    "contact": "1-800-656-4673",
                    "description": "24/7 confidential support",
                },
            },
        }

        # Trusted adults guidance
        self.trusted_adults_guidance = {
            "general": [
                "A parent or family member you trust",
                "A teacher or school counselor",
                "A coach or mentor",
            ],
            "abuse": [
                "A trusted teacher or school counselor",
                "Another family member you feel safe with",
                "A coach, mentor, or other trusted adult",
            ],
        }

        # Closing messages
        self.closing_messages = {
            "suicide": "You matter, and there are people who want to help you feel better. Please reach out to them. 💙",
            "self_harm": "You deserve support and care. Please reach out to someone who can help. 💙",
            "abuse_physical": "What you told me is important, and there are people who can help keep you safe. Please reach out to them. 💙",
            "abuse_emotional": "You deserve to be treated with kindness and respect. Please reach out to someone who can help. 💙",
            "abuse_sexual": "You are not alone, and this is not your fault. Please reach out to someone who can help keep you safe. 💙",
        }

        logger.info("CrisisResponseTemplates initialized")

    def get_response(
        self,
        category: str,
        user_name: Optional[str] = None,
        personalize: bool = True
    ) -> str:
        """
        Get crisis response for a specific category

        Args:
            category: Crisis category (suicide, self_harm, abuse_physical, abuse_emotional, abuse_sexual)
            user_name: Optional user name for personalization
            personalize: Whether to include personalization

        Returns:
            Complete crisis response message
        """
        category_lower = category.lower()

        # Validate category
        if category_lower not in self.concern_openings:
            logger.warning(f"Unknown crisis category: {category}, using generic response")
            return self._get_generic_crisis_response(user_name)

        # Build response components
        components = []

        # 1. Opening with concern
        opening = self.concern_openings[category_lower]
        components.append(opening)

        # 2. Validation message
        validation = self.validation_messages[category_lower]
        components.append(validation)

        # 3. Trusted adults guidance
        components.append("")  # Blank line
        if category_lower in ["abuse_physical", "abuse_emotional", "abuse_sexual"]:
            components.append("Please talk to a trusted adult right away - this could be:")
            for adult in self.trusted_adults_guidance["abuse"]:
                components.append(f"- {adult}")
        else:
            components.append("Please talk to a trusted adult right away - like your parents, a teacher, or school counselor. They care about you and can really help.")

        # 4. Crisis resources
        components.append("")  # Blank line
        if category_lower in self.crisis_resources:
            resources = self.crisis_resources[category_lower]

            # For abuse, add emergency services note first if physical
            if category_lower == "abuse_physical":
                components.append("If you're not sure who to talk to or if you're in immediate danger:")
            else:
                components.append("If you need to talk to someone right now:")

            # Primary resource
            primary = resources["primary"]
            components.append(f"- {primary['name']}: {primary['contact']}")

            # Secondary resource
            secondary = resources["secondary"]
            components.append(f"- {secondary['name']}: {secondary['contact']}")

        # 5. Closing message
        components.append("")  # Blank line
        closing = self.closing_messages[category_lower]
        components.append(closing)

        return "\n".join(components)

    def get_suicide_response(self, user_name: Optional[str] = None) -> str:
        """
        Get suicide/suicidal ideation crisis response

        Args:
            user_name: Optional user name for personalization

        Returns:
            Suicide crisis response message
        """
        return self.get_response("suicide", user_name)

    def get_self_harm_response(self, user_name: Optional[str] = None) -> str:
        """
        Get self-harm crisis response

        Args:
            user_name: Optional user name for personalization

        Returns:
            Self-harm crisis response message
        """
        return self.get_response("self_harm", user_name)

    def get_physical_abuse_response(self, user_name: Optional[str] = None) -> str:
        """
        Get physical abuse crisis response

        Args:
            user_name: Optional user name for personalization

        Returns:
            Physical abuse crisis response message
        """
        return self.get_response("abuse_physical", user_name)

    def get_emotional_abuse_response(self, user_name: Optional[str] = None) -> str:
        """
        Get emotional abuse crisis response

        Args:
            user_name: Optional user name for personalization

        Returns:
            Emotional abuse crisis response message
        """
        return self.get_response("abuse_emotional", user_name)

    def get_sexual_abuse_response(self, user_name: Optional[str] = None) -> str:
        """
        Get sexual abuse crisis response

        Args:
            user_name: Optional user name for personalization

        Returns:
            Sexual abuse crisis response message
        """
        return self.get_response("abuse_sexual", user_name)

    def _get_generic_crisis_response(self, user_name: Optional[str] = None) -> str:
        """
        Get generic crisis response for unknown categories

        Args:
            user_name: Optional user name for personalization

        Returns:
            Generic crisis response message
        """
        return """I'm really concerned about what you just shared with me. This sounds like something serious that I'm not equipped to help with.

Please talk to a trusted adult right away - like your parents, a teacher, or school counselor. They care about you and can provide the help you need.

If you need to talk to someone right now:
- Crisis Text Line: Text HOME to 741741
- National Suicide Prevention Lifeline: 988 (call or text)

You deserve support and care. Please reach out to someone who can help. 💙"""

    def get_resources_for_category(self, category: str) -> Dict:
        """
        Get crisis resources for a specific category

        Args:
            category: Crisis category

        Returns:
            Dictionary with resource information
        """
        category_lower = category.lower()

        if category_lower not in self.crisis_resources:
            logger.warning(f"Unknown crisis category: {category}, returning generic resources")
            return {
                "primary": {
                    "name": "Crisis Text Line",
                    "contact": "Text HOME to 741741",
                    "description": "Free, 24/7 crisis support via text",
                },
                "secondary": {
                    "name": "National Suicide Prevention Lifeline",
                    "contact": "988 (call or text)",
                    "description": "24/7 confidential support",
                },
            }

        return self.crisis_resources[category_lower]

    def get_all_resources(self) -> Dict:
        """
        Get all crisis resources across all categories

        Returns:
            Dictionary mapping categories to resources
        """
        return self.crisis_resources

    def get_stats(self) -> Dict:
        """
        Get statistics about crisis response templates

        Returns:
            Dictionary with template statistics
        """
        return {
            "total_categories": len(self.concern_openings),
            "categories": list(self.concern_openings.keys()),
            "total_resources": sum(len(resources) for resources in self.crisis_resources.values()),
            "resource_categories": list(self.crisis_resources.keys()),
        }


# Global instance
crisis_response_templates = CrisisResponseTemplates()


# Convenience functions
def get_response(category: str, user_name: Optional[str] = None) -> str:
    """Get crisis response for category"""
    return crisis_response_templates.get_response(category, user_name)


def get_suicide_response(user_name: Optional[str] = None) -> str:
    """Get suicide crisis response"""
    return crisis_response_templates.get_suicide_response(user_name)


def get_self_harm_response(user_name: Optional[str] = None) -> str:
    """Get self-harm crisis response"""
    return crisis_response_templates.get_self_harm_response(user_name)


def get_physical_abuse_response(user_name: Optional[str] = None) -> str:
    """Get physical abuse crisis response"""
    return crisis_response_templates.get_physical_abuse_response(user_name)


def get_emotional_abuse_response(user_name: Optional[str] = None) -> str:
    """Get emotional abuse crisis response"""
    return crisis_response_templates.get_emotional_abuse_response(user_name)


def get_sexual_abuse_response(user_name: Optional[str] = None) -> str:
    """Get sexual abuse crisis response"""
    return crisis_response_templates.get_sexual_abuse_response(user_name)


def get_resources_for_category(category: str) -> Dict:
    """Get resources for crisis category"""
    return crisis_response_templates.get_resources_for_category(category)


def get_all_resources() -> Dict:
    """Get all crisis resources"""
    return crisis_response_templates.get_all_resources()


def get_stats() -> Dict:
    """Get crisis response template statistics"""
    return crisis_response_templates.get_stats()
