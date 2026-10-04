from fastapi import HTTPException, status

class VerificationTokenNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, 'Verification token not found. That token may be forged.')

class VerificationTokenNotEqualError(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_400_BAD_REQUEST, 'The verification token was found, but it does not match the saved one. That token may be forged.')
