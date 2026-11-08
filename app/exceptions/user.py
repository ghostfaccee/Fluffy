from fastapi import HTTPException, status

class UserDoesNotExists(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, 'User does not exists')

class InvalidPassword(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, 'Invalid password')

class UsernameAlreadyTaken(HTTPException):
    def __init__(self):
        self.field = 'username'
        super().__init__(status.HTTP_409_CONFLICT, 'Username already taken')

class EmailAlreadyTaken(HTTPException):
    def __init__(self):
        self.field = 'email'
        super().__init__(status.HTTP_409_CONFLICT, 'Email already taken')

class UserAlreadyExists(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_409_CONFLICT, 'User already exists')

class InvalidAvatarKey(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_400_BAD_REQUEST, 'This is someone elses avatar key. The user attempted to claim someone elses avatar key for themselves.')
