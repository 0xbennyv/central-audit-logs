import requests
import json
import os
from datetime import date, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()

chrome_options = webdriver.ChromeOptions()
# Headless hides chome
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--incognito")

driver = webdriver.Chrome(options=chrome_options)

def createsession():
    print("Logging into Sophos Central.")
    # Login form with the redirect URL to Sophos Central.
    driver.get('https://login.sophos.com/login.sophos.com/oauth2/v2.0/authorize?p=B2C_1A_signup_signin_with_federation&client_id=6393a2fc-4a6b-4dce-989a-db1f013688da&redirect_uri=https%3A%2F%2Fcentral.sophos.com%2Fmanage%2Flogin%2Fazureb2c&scope=openid&response_type=id_token&prompt=login')
    # Define and wait for form field availiblity.
    frmusername = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.ID, "signInName"))
    )
    frmpassword = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.ID, "password"))
    )
    frmbutton = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.ID, "next"))
    )
    # Send Username, Password and Click the Button.
    frmusername.send_keys(os.getenv("CENTRAL_USERNAME"))
    frmpassword.send_keys(os.getenv("CENTRAL_PASSWORD"))
    frmbutton.click()
    # Add a wait until Sophos Central Loads
    print("Logged in - Waiting for Central to Load")
    frmbutton = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.ID, "header-title-id"))
    )


def getcookies():
    # Build a DICT of the Selenium Cookies in a format the requests understands
    cookies = {}
    selenium_cookies = driver.get_cookies()
    for cookie in selenium_cookies:
        cookies[cookie['name']] = cookie['value']
    return cookies


def getauditlogs():
    print("Getting Audit Logs")
    cookies = getcookies()
    # response = requests.get('https://central.sophos.com/api/reports/audit', cookies=cookies)
    # https://central.sophos.com/api/reports/audit?ascending=false&from=2021-08-17T05:32:43.267Z&group=date&limit=50&offset=0&to=2021-08-24T05:32:43.267Z
    yesterday = date.today() + timedelta(days=-1)
    response = requests.get(f'https://central.sophos.com/api/reports/audit?ascending=false&from={yesterday}T00:00:0.000Z', cookies=cookies)
    if response.ok:
        data = json.loads(response.text)
        print("Success - Outputting File")
        savefile(data)
        # If you wanted to automatically send this to a SIEM  a function here that posts the data
        # sendtosiem(data)
    else:
        print(f"Error - Getting Central Logs HTTP Reponse Code:{response.status_code}")


# If you want this data to go to a SIEM a function would look like this but will requre some work
def sendtosiem(data):
    print("Sending to data to SIEM")
    url = "https://SIEM"
    headers = {
        "ContentType": "Application/JSON"
    }
    response = requests.post(url, headers=headers, data=data)
    if response.ok:
        print("Success - Sent data to SIEM")
    else:
        print(f"Error - Can't send data to SIEM HTTP Reponse Code:{response.status_code}")


def savefile(data):
    filename = date.today() + timedelta(days=-1)
    print(f"Saving Audit Log to {filename}")
    with open(f'{filename}.json', 'w') as file:
        json.dump(data, file, indent=4)


def configinit():
    centralusername = input("Please enter Sophos Central Username: ")
    centralpassword = input("Please enter Sophos Central Password: ")
    envfile = os.path.expanduser('.env')
    with open(envfile, 'w') as env:
        env.write(f'CENTRAL_USERNAME = {centralusername}\n')
        env.write(f'CENTRAL_PASSWORD = {centralpassword}\n')
    print("Credentials Initiated, please restart the script")

if __name__ == "__main__":
    if not os.path.exists('.env'):
        configinit()
    else:
        createsession()
        getauditlogs()
