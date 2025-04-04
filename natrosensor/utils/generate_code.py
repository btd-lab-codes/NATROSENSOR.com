import random

# Function for generating the otp code randomly
def generate_otp():
    return f"{random.randint(0, 999999):06d}"