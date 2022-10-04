from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import Twilio
import configparser
from webdriver_manager.chrome import ChromeDriverManager
import platform, os, sys, random, time, inspect, re

url = r"https://login.ualberta.ca/module.php/core/loginuserpass.php?AuthState=_f8c61ba817f1cb623585957925ae11d53454cb486b%3Ahttps%3A%2F%2Flogin.ualberta.ca%2Fsaml2%2Fidp%2FSSOService.php%3Fspentityid%3Dhttps%253A%252F%252Fwww.beartracks.ualberta.ca%252Fsimplesaml%252Fmodule.php%252Fsaml%252Fsp%252Fmetadata.php%252Fspprodbt%26cookieTime%3D1546112453%26RelayState%3Dhttps%253A%252F%252Fwww.beartracks.ualberta.ca%252Fuahebprd%252Fsignon.html"
chrome_path = r'open -a /Applications/Google\ Chrome.app %s'
url2 = r"https://www.beartracks.ualberta.ca/psp/uahebprd/EMPLOYEE/HRMS/c/ZSS_STUDENT_CENTER.ZSS_WATCH_LIST.GBL?FolderPath=PORTAL_ROOT_OBJECT.ZSS_ACADEMICS.ZSS_AC_PLAN.ZSS_WATCH_LIST_GBL_1&IsFolder=false&IgnoreParamTempl=FolderPath%2cIsFolder"


def main():
    #path = ''
    path = installDriver()
    shouldSend = True
    # Get information
    username = input("Enter beartracks username: ")
    password = input("Enter beartracks Password: ")
    phone = input("Enter phone number: ")
    if(input("Hide browser?(Y/N) ").lower() == "y"):
        headless = True
    else:
        headless = False
    # get the term and check conditions on it
    term = input("Specify the term(winter, fall, summer, spring): ").lower()
    if(not(term.__contains__('winter') or term.__contains__('spring') or term.__contains__('fall') or term.__contains__('summer'))):
        print("Invalid term.")
        sys.exit(0)

    counter = 1
    # Main loop controlling the program
    while True:
        # Run the driver to check the watch list
        openClasses, shouldSend, path = runDriver(username, password, path, headless, shouldSend, term, phone)
        # If class is open, call sendMessage
        if(len(openClasses) <= 0):
            print("No open classes. Trial #" + str(counter))
        elif(len(openClasses) > 0):
            status = ' '.join(openClasses) + " now open, ENROLL:     Text DONE to stop messages"
            shouldSend = Twilio.sendMessage(status, phone)
        time.sleep(random.randint(60,100))
        counter += 1


# Check for chrome driver location on device, and install if nonexistant
def installDriver():
    path = ''
    for i in ChromeDriverManager().install():
        path += i
        if(path.__contains__("found in")):
            path = ''
    if(platform.platform().lower().__contains__("windows")):
        path = path.replace("\\", '/')
    return path


# Runs the driver that basically checks the Url to see if the class is open
def runDriver(username, password, path, headless, shouldSend, term, phoneNumber):
    driver = None
    msg = ""
    openClasses = []
    try:
        chromeOptions = Options()
        # Headless mode to make it less intensive/intrusive
        if(headless):
            chromeOptions.add_argument("headless")
            chromeOptions.add_argument("--no-sandbox");
            chromeOptions.add_argument("--disable-dev-shm-usage");
        driver = webdriver.Chrome(path, options=chromeOptions)
        # Go to beartracks
        driver.get(url)
        driver.implicitly_wait(3)
        # Enter login info and click login
        driver.find_element_by_id('username').send_keys(username)
        driver.find_element_by_id('user_pass').send_keys(password)
        driver.find_element_by_css_selector('.btn.btn-default').click()
        driver.implicitly_wait(5)
        try:
            msg = driver.find_element_by_xpath('//*[@id="message"]').text

        except:
            pass
        if (msg.lower().__contains__('maintenance')):
            time.sleep(300)
        else:
            # Go to watchlist url
            driver.get(url2)
            driver.implicitly_wait(3)
            # Switch to the frame containing the radio buttons, find and click them
            driver.switch_to.frame(driver.find_element_by_xpath('/html/frameset/frameset/frame[2]'))
            try:
                pathToTerm = findTerms(term, driver)
                driver.find_element_by_xpath(pathToTerm).click()
                driver.find_element_by_xpath('//*[@id="DERIVED_SSS_SCT_SSR_PB_GO"]').click()
                print("Multiple terms available.")
            except Exception as e:
                print(e)
            driver.implicitly_wait(5)
            # Switch to the frame containing the status of the course and return if there is an image of open course
            try:
                driver.switch_to.default_content()
                driver.switch_to.frame(driver.find_element_by_xpath('/html/frameset/frameset/frame[2]'))
                openClasses = getOpenClasses(driver)
            except:
                print("No classes on watchlist.")
                driver.quit()
        driver.quit()
    # Send text message with error if bot crashes unexpectedly
    except Exception as e:
        print(e)
        if(str(e).__contains__('This version of ChromeDriver only supports Chrome version')):
            # Add this since the current chromedriver version doesn't work
            path = re.sub('/[0-9.]+/', '/74.0.3729.6/', path)
            print("Newest driver not supported, using", path, "instead.")
        elif(shouldSend):
            shouldSend = Twilio.sendMessage("Bot crashed! " + str(e) + " Text DONE to stop messages", phoneNumber)
        if(driver != None):
            driver.quit()
    return openClasses, shouldSend, path


# Retrieves all the open classes and returns an array of them
def getOpenClasses(driver):
    openClasses = []
    shouldIter = True
    i = 0
    # iterate over all classes on watchlist
    while shouldIter:
        try:
            path = '//*[@id="win0divDERIVED_REGFRM1_SSR_STATUS_LONG$' + str(i) + '"]/div/img'
            status = driver.find_element_by_xpath(path).get_attribute('src')
            # If the class is open, append class name to the open Classes list
            classPath = '//*[@id="DERIVED_REGFRM1_SSR_CLASSNAME_35$' + str(i) + '"]'
            if(status.lower().__contains__('open')):
                openClasses.append(driver.find_element_by_xpath(classPath).get_attribute('innerHTML'))
            else:
                print(driver.find_element_by_xpath(classPath).get_attribute('innerHTML'), "is closed.")
            i += 1
        except:
            shouldIter = False

    # if there are no closes, return error message and exit
    if(i==0):
        print("You have no classes on your watchlist for this term.")
        driver.quit()
        sys.exit()

    return openClasses


# returns the correct xPath for the requested term
def findTerms(reqTerm, driver):
    # Try each possible term and find the correct one
    for i in range(3):
        t = driver.find_element_by_xpath('//*[@id="TERM_CAR$' + str(i) + '"]').get_attribute('innerText')
        if(t.lower().__contains__(reqTerm)):
            return '//*[@id="SSR_DUMMY_RECV1$sels$' + str(i) + '$$0"]'
    # If we didn't find the term
    print("Term Not found.")
    driver.quit()
    sys.exit(0)


main()
