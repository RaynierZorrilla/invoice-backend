class DuplicateTrackingNumberError(Exception):
    def __init__(self, tracking_number: str):
        self.tracking_number = tracking_number
        super().__init__(f"Duplicate tracking number: {tracking_number}")


class InvalidStatusTransitionError(Exception):
    def __init__(self, from_status: str, to_status: str):
        self.from_status = from_status
        self.to_status = to_status
        super().__init__(
            f"Invalid status transition: {from_status!r} -> {to_status!r}"
        )
