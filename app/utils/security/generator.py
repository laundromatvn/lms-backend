import random
import string


def generate_password(length: int = 8) -> str:
    """
    Generate a random password.
    Password contains at least one uppercase letter, one lowercase letter and one digit.
    """
    password = []
    password.append(random.choice(string.ascii_uppercase))
    password.append(random.choice(string.ascii_lowercase))
    password.append(random.choice(string.digits))

    for _ in range(length - 3):
        password.append(random.choice(
            string.ascii_uppercase + string.ascii_lowercase + string.digits
        ))

    random.shuffle(password)

    return ''.join(password)


def generate_otp(length: int = 6) -> str:
    """
    Generate a random OTP.
    """
    return ''.join(random.choices(string.digits, k=length))
