from app.domain.enums import RequestStatus


class StatusTransitionRules:
    """Бизнес-правила перехода статусов: Новая → В работе → Выполнена."""

    ALLOWED_TRANSITIONS: dict[RequestStatus, set[RequestStatus]] = {
        RequestStatus.NEW: {RequestStatus.IN_PROGRESS},
        RequestStatus.IN_PROGRESS: {RequestStatus.DONE},
        RequestStatus.DONE: set(),
    }

    @classmethod
    def is_allowed(cls, current: RequestStatus, new: RequestStatus) -> bool:
        return new in cls.ALLOWED_TRANSITIONS.get(current, set())

    @classmethod
    def allowed_targets(cls, current: RequestStatus) -> set[RequestStatus]:
        return cls.ALLOWED_TRANSITIONS.get(current, set())
