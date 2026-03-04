"""Application-specific exceptions for HTTP error mapping."""


class CarouselNotFoundError(Exception):
    """Raised when carousel by id does not exist."""


class CarouselConflictError(Exception):
    """Raised when carousel exists but is not available for generation (e.g. not draft or active generation exists)."""
