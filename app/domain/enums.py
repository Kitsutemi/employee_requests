from enum import Enum


class RequestStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DONE = "done"

    @property
    def label(self) -> str:
        labels = {
            RequestStatus.NEW: "Новая",
            RequestStatus.IN_PROGRESS: "В работе",
            RequestStatus.DONE: "Выполнена",
        }
        return labels[self]
