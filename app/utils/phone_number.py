import re


def is_valid_phone_number(phone_number: str) -> bool:
    if not phone_number:
        return False

    phone_number = phone_number.strip()
    if not phone_number:
        return False
    
    if not re.match(r'^\+?[\d\s\-\(\)]{10,20}$', phone_number):
        return False
    
    return True


def format_phone_number(phone_number: str) -> str:
    """
    Format and normalize phone number by removing all non-digit characters.
    
    Examples:
        +84 909 090 909 -> 84909090909
        +84 909 090 909 -> 84909090909
        0909090909 -> 0909090909
        909090909 -> 909090909
        +1 (555) 123-4567 -> 15551234567
    
    Args:
        phone_number: Raw phone number string
        
    Returns:
        Normalized phone number with only digits
        
    Raises:
        ValueError: If phone number is empty or invalid
    """
    if not phone_number:
        raise ValueError("Phone number cannot be empty")
    
    # Strip whitespace
    phone_number = phone_number.strip()
    if not phone_number:
        raise ValueError("Phone number cannot be empty")
    
    # Remove all non-digit characters
    digits_only = re.sub(r'[^\d]', '', phone_number)
    
    if not digits_only:
        raise ValueError("Phone number must contain at least one digit")
    
    # Basic validation - phone numbers should be between 7 and 15 digits
    if len(digits_only) < 7 or len(digits_only) > 15:
        raise ValueError(f"Phone number must be between 7 and 15 digits, got {len(digits_only)}")
    
    return digits_only
