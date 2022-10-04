from twilio.rest import Client

TWILIO_NUMBER = ""
# Send a text to phone number using Twilio
def sendMessage(status, phone):
    # Your Account Sid and Auth Token from twilio.com/console
    account_sid = '' #ENTER ACCOUNT SID
    auth_token = ''#ENTER AUTH TOKEN
    client = Client(account_sid, auth_token)
    # Get messages incoming to see if any are STOP
    received = client.messages.list(to=TWILIO_NUMBER)
    for record in received:
        message = record.body
        print(message)
        record.delete()
        if (message.lower() == "done"):
            return False

    # Send message to user
    message = client.messages \
        .create(
        body=status,
        from_=TWILIO_NUMBER,
        to=phone)
    return True
