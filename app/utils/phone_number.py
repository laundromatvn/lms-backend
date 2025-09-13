"""
Phone number formatting utilities for consistent phone number handling.
"""

import re
from typing import Optional


def format_phone_number(phone_number: str) -> str:
    """
    Format phone number to a consistent format for storage and comparison.
    
    This function:
    1. Removes all whitespace and special characters
    2. Removes leading '+' if present
    3. Removes leading '0' if present (common in Vietnamese phone numbers)
    4. Returns clean numeric string
    
    Args:
        phone_number: Raw phone number string
        
    Returns:
        Formatted phone number string (digits only)
        
    Examples:
        format_phone_number("+84 123 456 789") -> "84123456789"
        format_phone_number("0123-456-789") -> "123456789"
        format_phone_number("(123) 456-7890") -> "1234567890"
    """
    if not phone_number:
        return ""
    
    # Strip whitespace
    phone_number = phone_number.strip()
    
    # Remove leading '+' if present
    if phone_number.startswith('+'):
        phone_number = phone_number[1:]
        
    # Remove leading '0' if present (common in Vietnamese phone numbers)
    if phone_number.startswith('0'):
        phone_number = phone_number[1:]
        
    # Remove all non-digit characters
    phone_number = re.sub(r'[^\d]', '', phone_number)
    
    return phone_number


def normalize_phone_for_authentication(phone_number: str) -> str:
    """
    Normalize phone number specifically for authentication purposes.
    
    This function ensures consistent phone number format for authentication
    by applying the same formatting used during user registration.
    
    Args:
        phone_number: Raw phone number string from user input
        
    Returns:
        Normalized phone number string for authentication
        
    Raises:
        ValueError: If phone number is invalid after formatting
    """
    formatted_phone = format_phone_number(phone_number)
    
    if not formatted_phone:
        raise ValueError("Phone number cannot be empty")
    
    # Basic validation - should be 9-15 digits (international standard)
    if not re.match(r'^\d{9,15}$', formatted_phone):
        raise ValueError("Invalid phone number format")
    
    return formatted_phone


def is_valid_phone_format(phone_number: str) -> bool:
    """
    Check if phone number has valid format.
    
    Args:
        phone_number: Phone number string to validate
        
    Returns:
        True if phone number format is valid, False otherwise
    """
    try:
        normalized = normalize_phone_for_authentication(phone_number)
        return len(normalized) >= 9 and len(normalized) <= 15
    except ValueError:
        return False


def format_phone_for_display(phone_number: str, country_code: str = "+84") -> str:
    """
    Format phone number for display purposes.
    
    Args:
        phone_number: Raw or formatted phone number
        country_code: Country code to prepend (default: +84 for Vietnam)
        
    Returns:
        Formatted phone number for display
        
    Examples:
        format_phone_for_display("123456789") -> "+84 123 456 789"
        format_phone_for_display("84123456789") -> "+84 123 456 789"
    """
    formatted = format_phone_number(phone_number)
    
    if not formatted:
        return ""
    
    # Remove country code if already present
    if formatted.startswith("84") and len(formatted) > 9:
        formatted = formatted[2:]
    
    # Format with spaces for readability
    if len(formatted) >= 9:
        # Format as XXX XXX XXX for 9+ digits
        formatted = re.sub(r'(\d{3})(\d{3})(\d+)', r'\1 \2 \3', formatted)
    
    return f"{country_code} {formatted}"
