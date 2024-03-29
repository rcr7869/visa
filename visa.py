import time
import json
import random
import requests
import configparser
import re,uuid
from datetime import datetime
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as Wait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

#from selenium import webdriver
#from selenium.webdriver.chrome.service import Service

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from embassy import *

config = configparser.ConfigParser()
config.read('config.ini')

# Personal Info:
# Account and current appointment info from https://ais.usvisa-info.com
#USERNAME = config['PERSONAL_INFO']['USERNAME']
#PASSWORD = config['PERSONAL_INFO']['PASSWORD']
# Find SCHEDULE_ID in re-schedule page link:
# https://ais.usvisa-info.com/en-am/niv/schedule/{SCHEDULE_ID}/appointment
SCHEDULE_ID = config['PERSONAL_INFO']['SCHEDULE_ID']
# Target Period:
PRIOD_START = config['PERSONAL_INFO']['PRIOD_START']
PRIOD_END = config['PERSONAL_INFO']['PRIOD_END']
# Embassy Section:
YOUR_EMBASSY = config['PERSONAL_INFO']['YOUR_EMBASSY'] 
EMBASSY = Embassies[YOUR_EMBASSY][0]
FACILITY_ID = Embassies[YOUR_EMBASSY][1]
REGEX_CONTINUE = Embassies[YOUR_EMBASSY][2]

# Notification:
# Get email notifications via https://sendgrid.com/ (Optional)
SENDGRID_API_KEY = config['NOTIFICATION']['SENDGRID_API_KEY']
# Get push notifications via https://pushover.net/ (Optional)
PUSHOVER_TOKEN = config['NOTIFICATION']['PUSHOVER_TOKEN']
PUSHOVER_USER = config['NOTIFICATION']['PUSHOVER_USER']
# Get push notifications via PERSONAL WEBSITE http://yoursite.com (Optional)
PERSONAL_SITE_USER = config['NOTIFICATION']['PERSONAL_SITE_USER']
PERSONAL_SITE_PASS = config['NOTIFICATION']['PERSONAL_SITE_PASS']
PUSH_TARGET_EMAIL = config['NOTIFICATION']['PUSH_TARGET_EMAIL']
PERSONAL_PUSHER_URL = config['NOTIFICATION']['PERSONAL_PUSHER_URL']

# Time Section:
minute = 60
hour = 60 * minute
# Time between steps (interactions with forms)
STEP_TIME = 0.5
# Time between retries/checks for available dates (seconds)
RETRY_TIME_L_BOUND = config['TIME'].getfloat('RETRY_TIME_L_BOUND')
RETRY_TIME_U_BOUND = config['TIME'].getfloat('RETRY_TIME_U_BOUND')
# Cooling down after WORK_LIMIT_TIME hours of work (Avoiding Ban)
WORK_LIMIT_TIME = config['TIME'].getfloat('WORK_LIMIT_TIME')
WORK_COOLDOWN_TIME = config['TIME'].getfloat('WORK_COOLDOWN_TIME')
# Temporary Banned (empty list): wait COOLDOWN_TIME hours
BAN_COOLDOWN_TIME = config['TIME'].getfloat('BAN_COOLDOWN_TIME')

# CHROMEDRIVER
# Details for the script to control Chrome
LOCAL_USE = config['CHROMEDRIVER'].getboolean('LOCAL_USE')
# Optional: HUB_ADDRESS is mandatory only when LOCAL_USE = False
HUB_ADDRESS = config['CHROMEDRIVER']['HUB_ADDRESS']

#https://ais.usvisa-info.com/en-mx/niv/schedule/51702762/payment
SIGN_IN_LINK = f"https://ais.usvisa-info.com/{EMBASSY}/niv/users/sign_in"
#PAYMENT_LINK = f"https://ais.usvisa-info.com/{EMBASSY}/niv/schedule/51702762/payment"
#PAYMENT_LINK = f"https://ais.usvisa-info.com/{EMBASSY}/niv/schedule/51742857/payment"
#PAYMENT_LINK = f"https://ais.usvisa-info.com/{EMBASSY}/niv/schedule/51832735/payment"
#PAYMENT_LINK = f"https://ais.usvisa-info.com/{EMBASSY}/niv/schedule/51834450/payment"

APPOINTMENT_URL = f"https://ais.usvisa-info.com/{EMBASSY}/niv/schedule/{SCHEDULE_ID}/appointment"
DATE_URL = f"https://ais.usvisa-info.com/{EMBASSY}/niv/schedule/{SCHEDULE_ID}/appointment/days/{FACILITY_ID}.json?appointments[expedite]=false"
TIME_URL = f"https://ais.usvisa-info.com/{EMBASSY}/niv/schedule/{SCHEDULE_ID}/appointment/times/{FACILITY_ID}.json?date=%s&appointments[expedite]=false"
SIGN_OUT_LINK = f"https://ais.usvisa-info.com/{EMBASSY}/niv/users/sign_out"


MAC = -1
accounts = {
    "10": {
        0: ["intheend7869@gmail.com", "123456789aA.", "51702762"],
        1: ["cuenta.superior52@gmail.com", "123456789aA.", "52283977"],
        2: ["cuenta.superior55@gmail.com", "123456789aA.", "52284975"],
        3: ["cuenta.superior59@gmail.com", "123456789aA.", "52285006"],
    },
    "19": {
        0: ["johnsmith78666@mail.com", "12345678", "51742857"],
        1: ["cuenta.superior51@gmail.com", "123456789aA.", "51834450"],
        2: ["cuenta.superior54@gmail.com", "123456789aA.", "52284389"],
        3: ["cuenta.superior56@gmail.com", "123456789aA.", "52284981"],
    },
    "20": {
        0: ["cuenta.superior50@gmail.com", "123456789aA.", "51832735"],
        1: ["cuenta.superior53@gmail.com", "123456789aA.", "52284290"],
        2: ["cuenta.superior58@gmail.com", "123456789aA.", "52285000"],
        3: ["cuenta.superior57@gmail.com", "123456789aA.", "52284994"],
    },
    "11": {
        0: ["account1@solucionesinfogdl.com", "123456789aA.", "52575783"],
        1: ["account2@solucionesinfogdl.com", "123456789aA.", "52576077"],
        2: ["account7@solucionesinfogdl.com", "123456789aA.", "52579416"],
        3: ["syedumarhayyatshahji2@gmail.com", "123456789aA.", "52666852"],
    },
    "12": {
        0: ["account10@solucionesinfogdl.com", "123456789aA.", "52615048"],
        1: ["account11@solucionesinfogdl.com", "123456789aA.", "52623486"],
        2: ["account12@solucionesinfogdl.com", "123456789aA.", "52631459"],
        3: ["alexvaus126@gmail.com", "123456789aA.", "52667629"],
    },
    "13": {
        0: ["account13@solucionesinfogdl.com", "123456789aA.", "52631541"],
        1: ["account14@solucionesinfogdl.com", "123456789aA.", "52631583"],
        2: ["Manningsarah417@gmail.com", "123456789aA.", "52667708"],
        3: ["chapmanpiper798@gmail.com", "123456789aA.", "52667780"],
    },
    "14": {
        0: ["kleinlaura75@gmail.com", "123456789aA.", "52683322"],
        1: ["Marymoore2092@gmail.com", "123456789aA.", "52682968"],
        2: ["rubyrose2991@gmail.com", "123456789aA.", "52667848"],
        3: ["felixpaul1235@gmail.com", "123456789aA.", "52679864"],
    },
    "15": {
        0: ["mcintoshmaggie73@gmail.com", "123456789aA.", "52682729"],
        1: ["jasonhartley806@gmail.com", "123456789aA.", "52679973"],
        2: ["bethllamas9@gmail.com", "123456789aA.", "52679943"],
        3: ["hongsiako@gmail.com", "123456789aA.", "52679962"],
    },
    "55": {
        0: ["mcintoshmaggie73@gmail.com", "123456789aA.", "55519124"],
        1: ["jasonhartley806@gmail.com", "123456789aA.", "55520516"],
        2: ["bethllamas9@gmail.com", "123456789aA.", "55520620"],
        3: ["hongsiako@gmail.com", "123456789aA.", "55520678"],
    }
}

JS_SCRIPT = ("var req = new XMLHttpRequest();"
             f"req.open('GET', '%s', false);"
             "req.setRequestHeader('Accept', 'application/json, text/javascript, */*; q=0.01');"
             "req.setRequestHeader('X-Requested-With', 'XMLHttpRequest');"
             f"req.setRequestHeader('Cookie', '_yatri_session=%s');"
             "req.send(null);"
             "return req.responseText;")

def send_notification(title, msg):
    print(f"Sending notification!")
    if SENDGRID_API_KEY:
        USERNAME="something@gmail.com"
        message = Mail(from_email=USERNAME, to_emails=USERNAME, subject=msg, html_content=msg)
        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            print("outer error")
            print(e)
    if PUSHOVER_TOKEN:
        url = "https://api.pushover.net/1/messages.json"
        data = {
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "message": msg
        }
        requests.post(url, data)
    if PERSONAL_SITE_USER:
        url = PERSONAL_PUSHER_URL
        data = {
            "title": "VISA - " + str(title),
            "user": PERSONAL_SITE_USER,
            "pass": PERSONAL_SITE_PASS,
            "email": PUSH_TARGET_EMAIL,
            "msg": msg,
        }
        requests.post(url, data)


def auto_action(label, find_by, el_type, action, value, sleep_time=0):
    print("\t"+ label +":", end="")
    # Find Element By
    match find_by.lower():
        case 'id':
            item = driver.find_element(By.ID, el_type)
        case 'name':
            item = driver.find_element(By.NAME, el_type)
        case 'class':
            item = driver.find_element(By.CLASS_NAME, el_type)
        case 'xpath':
            item = driver.find_element(By.XPATH, el_type)
        case _:
            return 0
    # Do Action:
    match action.lower():
        case 'send':
            item.send_keys(value)
        case 'click':
            item.click()
        case _:
            return 0
    print("\t\tCheck!")
    if sleep_time:
        time.sleep(sleep_time)


def stillrunning():
    noww = datetime.now()
    current_timee = noww.strftime("%M")
    current_timeee = noww.strftime("%H:%M:%S")
    if int(current_timee) % 10 == 0:
        send_notification("title", "still running. "+ mac+ "  "+ current_timeee)
        print("still running")


counter = 0


def start_process():
    # Bypass reCAPTCHA
    global counter
    
    print("Starting time ", datetime.now().strftime("%-I:%M:%S"))
    print("mac num ", MAC, counter)
    info_logger(LOG_FILE_NAME, mac)
    USERNAME = accounts[MAC][counter][0]
    PASSWORD = accounts[MAC][counter][1]
    PAYMENT_LINK = accounts[MAC][counter][2]

    print(USERNAME, PASSWORD, PAYMENT_LINK,counter)
    PAYMENT_LINK = f"https://ais.usvisa-info.com/{EMBASSY}/niv/schedule/{PAYMENT_LINK}/payment"
    print(PAYMENT_LINK)
    #time.sleep(120)
    driver.get(SIGN_IN_LINK)
    time.sleep(STEP_TIME)
    Wait(driver, 60).until(EC.presence_of_element_located((By.NAME, "commit")))
    auto_action("Click bounce", "xpath", '//a[@class="down-arrow bounce"]', "click", "", STEP_TIME)
    auto_action("Email", "id", "user_email", "send", USERNAME, STEP_TIME)
    auto_action("Password", "id", "user_password", "send", PASSWORD, STEP_TIME)
    auto_action("Privacy", "class", "icheckbox", "click", "", STEP_TIME)
    auto_action("Enter Panel", "name", "commit", "click", "", STEP_TIME)
    #Wait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//a[contains(text(), '" + REGEX_CONTINUE + "')]")))
    print("\n\tlogin successful!\n")
    time.sleep(5)
    print("\n\t after login successful!\n")

    while 1:
        try:
            driver.get(PAYMENT_LINK)
            all = driver.find_element(By.CLASS_NAME,"for-layout").text
            response = driver.find_element(By.CLASS_NAME,"for-layout").text.split("\n")
            info_logger(LOG_FILE_NAME, all)
            now = datetime.now()
            appointmentsCounter = 0
            current_time = now.strftime("%-I:%M:%S")
            for cita in response:
#                if len(cita.split(",")) > 1:
#                    if cita.split(",")[1].strip() == '2023':
#                        send_notification(cita, cita+ " "+current_time+" MAC:"+MAC)
                if "Mexico" in cita and "February" in cita:
                    send_notification(cita, cita+ " "+current_time+" MAC:"+MAC)
                if "Mexico" in cita and "March" in cita:
                    send_notification(cita, cita+ " "+current_time+" MAC:"+MAC)
                if "Appointments" in cita:
                    appointmentsCounter = appointmentsCounter + 1
            if appointmentsCounter > 8:
                counter = (counter+1) % len(accounts[MAC])
                raise Exception("No appointments")
            print(current_time)
            info_logger(LOG_FILE_NAME, current_time)
            #stillrunning()
            print(all)
            time.sleep(120)
        except Exception as e:
            print(e)
            #send_notification("error", "error: ")
            time.sleep(300)
            start_process()

def reschedule(date):
    time = get_time(date)
    driver.get(APPOINTMENT_URL)
    headers = {
        "User-Agent": driver.execute_script("return navigator.userAgent;"),
        "Referer": APPOINTMENT_URL,
        "Cookie": "_yatri_session=" + driver.get_cookie("_yatri_session")["value"]
    }
    data = {
        "utf8": driver.find_element(by=By.NAME, value='utf8').get_attribute('value'),
        "authenticity_token": driver.find_element(by=By.NAME, value='authenticity_token').get_attribute('value'),
        "confirmed_limit_message": driver.find_element(by=By.NAME, value='confirmed_limit_message').get_attribute('value'),
        "use_consulate_appointment_capacity": driver.find_element(by=By.NAME, value='use_consulate_appointment_capacity').get_attribute('value'),
        "appointments[consulate_appointment][facility_id]": FACILITY_ID,
        "appointments[consulate_appointment][date]": date,
        "appointments[consulate_appointment][time]": time,
    }
    r = requests.post(APPOINTMENT_URL, headers=headers, data=data)
    if(r.text.find('Successfully Scheduled') != -1):
        title = "SUCCESS"
        msg = f"Rescheduled Successfully! {date} {time}"
    else:
        title = "FAIL"
        msg = f"Reschedule Failed!!! {date} {time}"
    return [title, msg]


def get_date():
    # Requesting to get the whole available dates
    session = driver.get_cookie("_yatri_session")["value"]
    script = JS_SCRIPT % (str(DATE_URL), session)
    content = driver.execute_script(script)
    return json.loads(content)

def get_time(date):
    time_url = TIME_URL % date
    session = driver.get_cookie("_yatri_session")["value"]
    script = JS_SCRIPT % (str(time_url), session)
    content = driver.execute_script(script)
    data = json.loads(content)
    time = data.get("available_times")[-1]
    print(f"Got time successfully! {date} {time}")
    return time


def is_logged_in():
    content = driver.page_source
    if(content.find("error") != -1):
        return False
    return True


def get_available_date(dates):
    # Evaluation of different available dates
    def is_in_period(date, PSD, PED):
        new_date = datetime.strptime(date, "%Y-%m-%d")
        result = ( PED > new_date and new_date > PSD )
        # print(f'{new_date.date()} : {result}', end=", ")
        return result
    
    PED = datetime.strptime(PRIOD_END, "%Y-%m-%d")
    PSD = datetime.strptime(PRIOD_START, "%Y-%m-%d")
    for d in dates:
        date = d.get('date')
        if is_in_period(date, PSD, PED):
            return date
    print(f"\n\nNo available dates between ({PSD.date()}) and ({PED.date()})!")


def info_logger(file_path, log):
    # file_path: e.g. "log.txt"
    with open(file_path, "a") as file:
        file.write(str(datetime.now().time()) + ":\n" + log + "\n")


if LOCAL_USE:
    #driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    #service = Service()
    #options = webdriver.ChromeOptions()
    #options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    #driver = webdriver.Chrome(service=service, options=options)
    print("if")
else:
    driver = webdriver.Remote(command_executor=HUB_ADDRESS, options=webdriver.ChromeOptions())


if __name__ == "__main__":

    current_time = datetime.now().strftime("%-I:%M:%S")
    print(current_time)
    try:
        mac = (':'.join(re.findall('..', '%012x' % uuid.getnode())))
    except Exception as e:
        print(e)
    print("starting = ",mac)
    print("mac number == ",os.getenv('MAC'))
    MAC = os.getenv('MAC')

    first_loop = True
    while 1:
        LOG_FILE_NAME = "log_" + str(datetime.now().date()) + ".txt"
        if first_loop:
            t0 = time.time()
            total_time = 0
            Req_count = 0
            while 1:
                try:
                    print("starting")
                    service = Service()
                    options = webdriver.ChromeOptions()
                    if int(MAC) > 9:
                        options.binary_location = "/usr/bin/google-chrome-stable"
                        print("using linux")
                    else:
                        print("using mac")
                        options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                    driver = webdriver.Chrome(service=service, options=options)
                    start_process()
                except Exception as e:
                    #time.sleep(WORK_COOLDOWN_TIME * hour)
                    driver.stop_client()
                    driver.quit()
                    time.sleep(120)
                    print(e)

            first_loop = False
        Req_count += 1
        try:
            msg = "-" * 60 + f"\nRequest count: {Req_count}, Log time: {datetime.today()}\n"
            print(msg)
            info_logger(LOG_FILE_NAME, msg)
            dates = get_date()
            if not dates:
                # Ban Situation
                msg = f"List is empty, Probabely banned!\n\tSleep for {BAN_COOLDOWN_TIME} hours!\n"
                print(msg)
                info_logger(LOG_FILE_NAME, msg)
                send_notification("BAN", msg)
                driver.get(SIGN_OUT_LINK)
                time.sleep(BAN_COOLDOWN_TIME * hour)
                first_loop = True
            else:
                # Print Available dates:
                msg = ""
                for d in dates:
                    msg = msg + "%s" % (d.get('date')) + ", "
                msg = "Available dates:\n"+ msg
                print(msg)
                info_logger(LOG_FILE_NAME, msg)
                date = get_available_date(dates)
                if date:
                    # A good date to schedule for
                    END_MSG_TITLE, msg = reschedule(date)
                    break
                RETRY_WAIT_TIME = random.randint(RETRY_TIME_L_BOUND, RETRY_TIME_U_BOUND)
                t1 = time.time()
                total_time = t1 - t0
                msg = "\nWorking Time:  ~ {:.2f} minutes".format(total_time/minute)
                print(msg)
                info_logger(LOG_FILE_NAME, msg)
                if total_time > WORK_LIMIT_TIME * hour:
                    # Let program rest a little
                    send_notification("REST", f"Break-time after {WORK_LIMIT_TIME} hours | Repeated {Req_count} times")
                    driver.get(SIGN_OUT_LINK)
                    time.sleep(WORK_COOLDOWN_TIME * hour)
                    first_loop = True
                else:
                    msg = "Retry Wait Time: "+ str(RETRY_WAIT_TIME)+ " seconds"
                    print(msg)
                    info_logger(LOG_FILE_NAME, msg)
                    time.sleep(RETRY_WAIT_TIME)
        except:
            # Exception Occured
            msg = f"Break the loop after exception!\n"
            END_MSG_TITLE = "EXCEPTION"
            break

print(msg)
info_logger(LOG_FILE_NAME, msg)
send_notification(END_MSG_TITLE, msg)
driver.get(SIGN_OUT_LINK)
driver.stop_client()
driver.quit()



#driver.find_element(By.CLASS_NAME,"for-layout")
#driver.find_element(By.CLASS_NAME,"for-layout").text.split("\n")
#driver.find_element(By.CLASS_NAME,"for-layout").text.split("\n")[0].split(",")[1].strip() == '2023'
#exit()

#first = driver.find_element(By.CLASS_NAME,"for-layout").text.split("\n")[0]

#response = driver.find_element(By.CLASS_NAME,"for-layout").text.split("\n")[0].split(",")[1].strip()
#response = driver.find_element(By.CLASS_NAME,"for-layout").text.split("\n")[0].split(",")[1].strip() == '2023'



#print("", current_time, "|", first, "|", response == '2023')
