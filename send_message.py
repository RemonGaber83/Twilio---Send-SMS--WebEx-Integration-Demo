import os
from twilio.rest import Client
import flask
from flask import request
import logging
from flask import render_template
import webbrowser
import csv
from csv import writer
from datetime import date
from datetime import datetime
from pprint import pprint
import requests
import json
import sys

##############create webex web hook https://developer.webex.com/docs/api/v1/webhooks/create-a-webhook#######
################Send SMS http://127.0.0.1:5000/sendsms?to=+61448576622,+61448576622&body=ABC#########################################

webex_access_token = os.environ.get("TEAMS_ACCESS_TOKEN")
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "Authorization": "Bearer " + webex_access_token
}
Todaydate = (datetime.now()).strftime("%d/%m/%Y %H:%M:%S")
logging.basicConfig(level=logging.INFO)
# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = os.environ.get("twilio_account_sid")
auth_token = os.environ.get("twilio_auth_token")
client = Client(account_sid, auth_token)
#################################################################################
notification_webex_account= 'remon.gaber@kytec.com.au'
ngrok_url = 'http://48e870f5858a.ngrok.io'
twilio_phone_number = '+17813994155'
################################################################################
app = flask.Flask(__name__)
app.config["DEBUG"] = True

#########################Send SMS#####################################
def SendSMS(destination,smsbody):
    message = client.messages \
        .create(
            body=smsbody,
            from_=twilio_phone_number,
            status_callback= ngrok_url + '/MessageStatus',
            to=destination
        )

    #print(message)
    return(message)

#########################Log SMS Details#####################################
def SMSData(sms_data):
    with open('sms-data.csv', 'a', newline='') as f_object:
        writer_object = writer(f_object)
        writer_object.writerow(sms_data)
        f_object.close()

#########################Read SMS Details#####################################
def ReadSMSData():
    with open('sms-data.csv', newline='') as f_object:
        reader = csv.reader(f_object)
        message = []
        for row in reader:
            message.append((row[0],row[1],row[2],row[3],row[4]))
            #print(message)
    f_object.close()
    return (message)

#########################Validate Phone Number#####################################
def ValidatePhoneNumber(phone_number):
    if (len(phone_number) == 12) & (phone_number[0:4] == '+614') & phone_number[11:].isdecimal() == True:
        return (True)
    else:
        return (False)

#########################Twilio Webhook#####################################
@app.route("/MessageStatus", methods=['POST'])
def incoming_sms():
    message_id = request.values.get('MessageSid', None)
    message_status = request.values.get('MessageStatus', None)
    message_from = request.values.get('From', None)
    message_to = request.values.get('To', None)
    sms_data = [Todaydate,message_id,message_status,message_from,message_to]
    SMSData(sms_data)
    #logging.info('SID: {}, Status: {}'.format(message_id, message_status))
    webex_notification(sms_data)
    #webbrowser.get('windows-default').open('file://' + os.path.realpath('index.html?message=1'))
    return ('', 204)

#########################SMS Log#####################################
@app.route('/smslog')
def main():
    SMSData = ReadSMSData()
    #print(SMSData)
    data=SMSData
    del SMSData[0]
    return render_template('index.html', title='Home', data=data )

#########################Send SMS#####################################
@app.route('/sendsms', methods=['GET'])
def home():
    try:
        #to = "+" + request.args.get('to')[1:]
        phone_numbers = request.args.get('to')
        phone_numbers = list(phone_numbers.split(","))
        #print(phone_numbers)
        for i in phone_numbers:
            i = "+" + i[1:]
            if ValidatePhoneNumber(i) == False:
                return "<h1 style=\"color:red;\">Your message has been rejected</h1>"+"<p style=\"color:red;\">"+str(i)+" is invalid , the number format has to be +614XXXXXXXX</p>"
            else:
                body = request.args.get('body')
                message = SendSMS(str(i),body)
        return "<h1>Your message has been accepted</h1>"+"<p>Message ID: "+message.sid+"</p>"+"<p>Date: "+str(message.date_updated)+"</p>"+"<p>From: "+message.from_+"</p>"+"<p>To: "+message.to+"</p>"+"<p>Body: "+message.body+"</p>"+"<p>Message status: "+message.status+"</p>"+"<p>To check the message log status click on </p><a href=\"http://localhost:5000/smslog\">SMS Log</a>"
    except Exception as err:
       print(err)
       return "<h1>Application Failure</h1><p>"+err+"</p>"

#########################WebEx Integration#############################################################################

#########################GET API#####################################
def send_get(url, payload=None,js=True):

    if payload == None:
        request = requests.get(url, headers=headers)
    else:
        request = requests.get(url, headers=headers, params=payload)
    if js == True:
        request= request.json()
    return request

#########################POST API#####################################
def send_post(url, data):

    request = requests.post(url, json.dumps(data), headers=headers).json()
    return request

############################## Send WebEx Notification ###############
def webex_notification(message):
    apiUrl = 'https://webexapis.com/v1/messages'
    httpHeaders = { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + webex_access_token }
    #The variable will have a dictionary data-type with key:value pairs separated by commas. We will use two key parameters toPersonEmail and text, i.e. the recipient's email address and the message text:
    webex_message_contents= "Message ID: " + message[1] + " From: " + message[3] + " To: " + message[4] + " Message Status: " + message[2]
    body = { 'toPersonEmail': notification_webex_account, 'text': webex_message_contents }
    response = requests.post( url = apiUrl, json = body, headers = httpHeaders )

#########################BOT Help Me#####################################
def help_me():

    return "Sure! I can help. Below are the commands that I understand:<br/>" \
           "`send sms to:[+614XXXXXXXX,+614XXXXXXXX] Your Text Message` - To send SMS message to multiple phone numbers<br/>" 

#########################BOT Send SMS send sms tel:[+614XXXXXXXX,+614XXXXXXXX] Your Text Message#####################################
def webex_send_sms(message):
    to = message[(message.index("to:")+4):(message.index("]"))]
    phone_numbers = list(to.split(","))
    #print(phone_numbers)
    for i in phone_numbers:
        if ValidatePhoneNumber(i) == False:
            return "Your message has been rejected , the number format has to be +614XXXXXXXX.<br/>"\
                    "`Message Format - send sms to:[+614XXXXXXXX,+614XXXXXXXX] Your Text Message`"
        message_body = message[message.index("]")+1:]
        SendSMS(i,message_body)
    return "Your message has been queued to check the message log click on http://localhost:5000/smslog<br/>" 

#########################WebEx Teams Webhook#####################################
@app.route('/', methods=['GET', 'POST'])
def teams_webhook():
    if request.method == 'POST':
        webhook = request.get_json(silent=True)
        if webhook['resource'] == "memberships" and webhook['data']['personEmail'] == bot_email:
            send_post("https://api.ciscospark.com/v1/messages",
                            {
                                "roomId": webhook['data']['roomId'],
                                "markdown": (greetings() +
                                             "**Note This is a group room and you have to call "
                                             "me specifically with `@%s` for me to respond**" % bot_name)
                            }
                            )
        msg = None
        if "@webex.bot" not in webhook['data']['personEmail']:
            result = send_get(
                'https://api.ciscospark.com/v1/messages/{0}'.format(webhook['data']['id']))
            in_message = result.get('text', '').lower()
            in_message = in_message.replace(bot_name.lower() + " ", '')
            if in_message.startswith('send sms'):
                msg = webex_send_sms(in_message)
            elif in_message.startswith("repeat after me"):
                message = in_message.split('repeat after me ')[1]
                if len(message) > 0:
                    msg = "{0}".format(message)
                else:
                    msg = "I did not get that. Sorry!"
            else:
                msg = help_me()
            if msg != None:
                send_post("https://api.ciscospark.com/v1/messages",
                                {"roomId": webhook['data']['roomId'], "markdown": msg})
        return "true"
    elif request.method == 'GET':
        message = "<center><img src=\"https://cdn-images-1.medium.com/max/800/1*wrYQF1qZ3GePyrVn-Sp0UQ.png\" alt=\"Webex Teams Bot\" style=\"width:256; height:256;\"</center>" \
                  "<center><h2><b>Congratulations! Your <i style=\"color:#ff8000;\">%s</i> bot is up and running.</b></h2></center>" \
                  "<center><b><i>Don't forget to create Webhooks to start receiving events from Webex Teams!</i></b></center>" % bot_name
        return message



#################### Validate WebEx Token ##############################################
def main():
    global bot_email, bot_name
    if len(webex_access_token) != 0:
        test_auth = send_get("https://api.ciscospark.com/v1/people/me", js=False)
        if test_auth.status_code == 401:
            print("Looks like the provided access token is not correct.\n"
                  "Please review it and make sure it belongs to your bot account.\n"
                  "Do not worry if you have lost the access token. "
                  "You can always go to https://developer.webex.com/my-apps "
                  "and generate a new access token.")
            sys.exit()
        if test_auth.status_code == 200:
            test_auth = test_auth.json()
            bot_name = test_auth.get("displayName","")
            bot_email = test_auth.get("emails","")[0]
    else:
        print("'webex_access_token' variable is empty! \n"
              "Please populate it with bot's access token and run the script again.\n"
              "Do not worry if you have lost the access token. "
              "You can always go to https://developer.webex.com/my-apps "
              "and generate a new access token.")
        sys.exit()

    if "@webex.bot" not in bot_email:
        print("You have provided an access token which does not relate to a Bot Account.\n"
              "Please change for a Bot Account access token, view it and make sure it belongs to your bot account.\n"
              "Do not worry if you have lost the access token. "
              "You can always go to https://developer.webex.com/my-apps "
              "and generate a new access token for your Bot.")
        sys.exit()
    else:
        app.run()

if __name__ == "__main__":
    main()

#######################################################

