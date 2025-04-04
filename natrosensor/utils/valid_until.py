from django.utils.timezone import now
from datetime import timedelta

# Function for setting the validity 5 minutes from now
def valid_until():
    return now() + timedelta(minutes=5)