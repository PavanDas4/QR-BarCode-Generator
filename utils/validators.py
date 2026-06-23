from tkinter import messagebox


class ValidationError(ValueError):
    pass


def validate_data_text(data_text: str) -> None:
    if not data_text:
        raise ValidationError("QR / Barcode data is required.")
    if len(data_text) > 1024:
        raise ValidationError("Data text is too long. Please use a shorter value.")


def validate_heading(heading: str) -> None:
    if not heading:
        raise ValidationError("Heading is required.")
    if len(heading) > 25:
        raise ValidationError("Heading may not exceed 25 characters.")


def validate_description(description: str) -> None:
    if len(description) > 75:
        raise ValidationError("Description may not exceed 75 characters.")
