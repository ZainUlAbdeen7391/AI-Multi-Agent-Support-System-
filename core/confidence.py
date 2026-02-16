from enum import Enum


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceRouter:
    """
    Centralized confidence-based routing logic.
    """

    HIGH_THRESHOLD = 0.8
    MEDIUM_THRESHOLD = 0.5

    @classmethod
    def get_level(cls, confidence: float) -> ConfidenceLevel:
        if confidence >= cls.HIGH_THRESHOLD:
            return ConfidenceLevel.HIGH
        elif confidence >= cls.MEDIUM_THRESHOLD:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    @classmethod
    def requires_admin(cls, confidence: float) -> bool:
        """
        Determines if admin review is required.
        """
        return confidence < cls.HIGH_THRESHOLD

    @classmethod
    def routing_action(cls, confidence: float) -> str:
        """
        Returns system action based on confidence.
        """
        level = cls.get_level(confidence)

        if level == ConfidenceLevel.HIGH:
            return "auto_respond"
        elif level == ConfidenceLevel.MEDIUM:
            return "queue_for_admin"
        else:
            return "route_to_admin"
