# Install the Twilio Python library and Flask (a web framework):
# pip install twilio Flask

import os
from twilio.rest import Client
from flask import Flask, request, Response
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Your Account SID and Auth Token from twilio.com/console
# Set these as environment variables for security
account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
twilio_phone_number = os.environ.get("TWILIO_PHONE_NUMBER")  # Your Twilio phone number

if not all([account_sid, auth_token, twilio_phone_number]):
    print("Please set the TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER environment variables.")
    exit()

client = Client(account_sid, auth_token)

# Dictionary to store the expected next step for each patient's phone number
patient_state = {}

def send_sms(to_phone_number, message):
    """Sends an SMS message using Twilio."""
    try:
        message = client.messages.create(
            to=to_phone_number,
            from_=twilio_phone_number,
            body=message
        )
        print(f"SMS sent with SID: {message.sid}")
    except Exception as e:
        print(f"Error sending SMS: {e}")

def handle_patient_intake_start(patient_phone_number):
    """Starts the patient intake flow."""
    send_sms(patient_phone_number, "Hello! Welcome to our medical practice. My name is LiV, your virtual intake agent. Please reply with your name.")
    patient_state[patient_phone_number] = "waiting_for_name"

def handle_patient_intake_continue(patient_phone_number, patient_reply):
    """Continues the patient intake flow based on the current state."""
    current_state = patient_state.get(patient_phone_number)

    if current_state == "waiting_for_name":
        patient_name = patient_reply.strip()
        send_sms(patient_phone_number, f"Thank you, {patient_name}! Please reply with your OHIP number.")
        patient_state[patient_phone_number] = "waiting_for_ohip"
    elif current_state == "waiting_for_ohip":
        ohip_number = patient_reply.strip()
        send_sms(patient_phone_number, f"Thank you for your OHIP number: {ohip_number}. What type of appointment are you looking for today? (e.g., consultation, follow-up)")
        patient_state[patient_phone_number] = "waiting_for_appointment_type"
    elif current_state == "waiting_for_appointment_type":
        appointment_type = patient_reply.strip()
        send_sms(patient_phone_number, f"You are requesting a '{appointment_type}' appointment. Next available appointment time will be confirmed shortly by our staff. Please briefly describe the reason for your visit.")
        patient_state[patient_phone_number] = "waiting_for_complaint"
    elif current_state == "waiting_for_complaint":
        medical_complaint = patient_reply.strip()
        send_sms(patient_phone_number, f"Thank you for the summary: {medical_complaint}. This information will be shared with your care provider. Thank you for completing the initial intake. Our team will be in touch soon with further details.")
        del patient_state[patient_phone_number] # Intake complete, remove state
    else:
        send_sms(patient_phone_number, "Sorry, I'm not sure how to process that. Please try again or contact our office directly.")

@app.route("/sms", methods=["POST"])
def incoming_sms():
    """Handles incoming SMS messages from Twilio."""
    sender_phone_number = request.form['From']
    message_body = request.form['Body']

    if sender_phone_number not in patient_state:
        # Start a new intake if we haven't seen this number before
        handle_patient_intake_start(sender_phone_number)
    else:
        # Continue the existing intake flow
        handle_patient_intake_continue(sender_phone_number, message_body)

    return Response(status=200)

if __name__ == "__main__":
    # This part starts the Flask development server, which is suitable for running in an IDE.
    port = 5000
    print(f"Server is running on port {port}")
    app.run(debug=True, port=port)