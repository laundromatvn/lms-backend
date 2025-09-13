def format_phone_number(phone_number: str) -> str:
    phone_number = phone_number.strip()
    
    if phone_number.startswith('+'):
        phone_number = phone_number[1:]
        
    if phone_number.startswith('0'):
        phone_number = phone_number[1:]
        
    phone_number = phone_number.replace(' ', '')
    phone_number = phone_number.replace('-', '')
    phone_number = phone_number.replace('(', '')
    phone_number = phone_number.replace(')', '')
    
    return phone_number
