from fastapi import HTTPException, status

class UserDoesNotExists(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, 'User does not exists')

class InvalidPassword(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, 'Invalid password')

class UsernameAlreadyTaken(HTTPException):
    self.field = 'username'
    def __init__(self):
        super().__init__(status.HTTP_409_CONFLICT, 'Username already taken')

class EmailAlreadyTaken(HTTPException):
    def __init__(self):
        self.field = 'email'
        super().__init__(status.HTTP_409_CONFLICT, 'Email already taken')

class UserAlreadyExists(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_409_CONFLICT, f'User already exists')
