import string
import random


def generator_key(length: int = 5) -> str:
    characters = string.ascii_letters + string.digits
    key = ''.join(random.choices(characters, k=length))
    return key