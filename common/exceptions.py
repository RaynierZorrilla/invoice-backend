class DuplicateTrackingNumberError(Exception):
    def __init__(self, tracking_number: str):
        self.tracking_number = tracking_number
        super().__init__(f"Duplicate tracking number: {tracking_number}")
