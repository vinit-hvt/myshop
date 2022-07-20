import string
import random

def generateRandomString(length=30):
    generatedString = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    return generatedString


def isNumberValid(number, numberLenReq=None):
    number = str(number)
    if numberLenReq is not None and len(number) != numberLenReq:
        return False
    for digit in number:
        if not (digit >= '0' and digit <= '9'):
            return False
    return True