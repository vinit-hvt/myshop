from .models import Users
from .utils import isNumberValid

class validator():

    def __init__(self, formData):
        self.formData = formData
        self.isFormValid = True
        self.errorMessage = ""
        self.faultyKey = ''

    
    def __resetValues(self):
        self.isFormValid = True
        self.errorMessage = ""
        self.faultyKey = ''
    

    def validateSignupForm(self):

        self.__resetValues()
        if len(Users.objects.filter(username=self.formData['username'])): # Validating username #
            self.isFormValid = False
            self.errorMessage = "Username already Exists."
            self.faultyKey = 'username'
        elif len(Users.objects.filter(userEmail=self.formData['email'])): # Validating email #
            self.isFormValid = False
            self.errorMessage = "Email is already in use. Please try different email."
            self.faultyKey = 'email'
        elif not isNumberValid(self.formData['contact'], 10): # Validating contact number #
            self.isFormValid = False
            self.errorMessage = "Contact Number is not valid."
            self.faultyKey = 'contact'
        elif not isNumberValid(self.formData['zipCode']):  # Validating zip code #
            self.isFormValid = False
            self.errorMessage = "Zip Code is not valid."
            self.faultyKey = 'zipCode'