from fastapi import HTTPException, status

class InvalidCredentials(HTTPException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, 'Invalid username or password')

class UserNotActive(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, 'User not activated. Let them activate their account by clicking on the link in the email.')

class InvalidTokenError(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, 'Invalid token')

class TokenInBlacklistError(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, 'Token already in blacklist. Possible replay attack.')

class DifferentTokensError(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, 'Different tokens. Possible token forgery attack.')

class TokenNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, 'Token not found')

class LoginCodeIsNotEqual(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, 'Invalid code. Brute-force attack possible.')

class LoginCodeNotFound(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, 'Code not found. It may have expired.')

class InvalidAccessTokenError(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, 'Invalid access token')