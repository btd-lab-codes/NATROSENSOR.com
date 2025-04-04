from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password

from natrosensor.models import Otp
from .generate_code import generate_otp
from .valid_until import valid_until

# For creating and sending of OTP via email
def send_otp(email):
    # Obtain the value of the otp code based on the email provided
    otp_entry, created = Otp.objects.get_or_create(email=email)

    # Check if the otp code object is newly created or if the otp code is expired
    if created or not otp_entry.is_valid():
        # Generate the otp code
        otp_value = generate_otp()
        # The otp code must be encrypted to ensure the security
        otp_hashed = make_password(otp_value) 

        # Assign and save the value of the otp_hashed and validity onto the otp object
        otp_entry.code = otp_hashed
        otp_entry.valid_until = valid_until()
        otp_entry.save()

        # Creation message for sending the otp code via email
        subject = "Your OTP Code"
        message = f"Your One-Time Password (OTP) is: {otp_value}\n\nDo not share it with anyone."
        from_email = None
        headers={"Reply-To": "noreply-natrosensor@gmail.com"},

        # Sending the email to the email provider (Gmail)
        send_mail(subject, message, from_email, [email], headers)

        return True, otp_entry.valid_until
    else:
        return False, otp_entry.valid_until