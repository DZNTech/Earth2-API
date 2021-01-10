from rest_framework_api_key.permissions import HasAPIKey
from rest_framework_api_key.models import APIKey
from rest_framework.decorators import api_view,permission_classes
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import authenticate

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys

from .scrapper import scrape_settings,scrape_properties
from django.conf import settings
import os

@api_view(["POST"])
def get_api_key(request):
    name = request.data["name"]
    username = request.data["username"]
    password = request.data["password"]
    user = authenticate(username=username,password=password)
    if user is not None:
        api_key,key = APIKey.objects.create_key(name=name)
        return Response({"api_key": key},status=status.HTTP_200_OK)
    else:
        return Response({{"Error:Invalid Creadentials"}},status=status.HTTP_401_UNAUTHORIZED)



@api_view(["POST"])
@permission_classes([HasAPIKey])
def login(request):
    #try:
        selenium=None
        key=request.META['HTTP_AUTHORIZATION']
        user_email = request.data['email']
        user_password=request.data['password']
        print(settings.CHROMEDRIVER_PATH)
        print(settings.CHROME_BIN)
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.binary_location = settings.CHROME_BIN
        selenium = webdriver.Chrome(executable_path=settings.CHROMEDRIVER_PATH, chrome_options=chrome_options)

        #selenium = webdriver.Chrome(ChromeDriverManager().install(),chrome_options=chrome_options)
        selenium.get('https://app.earth2.io/login/auth0')

        email = selenium.find_element_by_id('username')
        password = selenium.find_element_by_id('password')

        submit = selenium.find_element_by_name('action')

        email.send_keys(user_email)
        password.send_keys(user_password)
        submit.send_keys(Keys.RETURN)
        try:
            if selenium.find_elements_by_id('error-element-password'):
                selenium.close()
                return Response({"error": "Invalid email or password"},status=status.HTTP_401_UNAUTHORIZED)
        except:
            pass
        selenium.get('https://app.earth2.io/#settings')
        html = selenium.page_source
        error,setting_json = scrape_settings(html)

        if setting_json.get("error"):
            selenium.close()
            return Response(setting_json,status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        selenium.close()
        return Response({"data": setting_json},status=status.HTTP_200_OK)
    
    #except:
        if selenium:
            selenium.close()
        return Response({"error":"Something went wrong"},status=status.HTTP_504_GATEWAY_TIMEOUT)



class element_has_value(object):
  """An expectation for checking that an element has a particular css class.

  locator - used to find the element
  returns the WebElement once it has the particular css class
  """
  def __init__(self, locator, tag_value):
    self.locator = locator
    self.tag_value = tag_value

  def __call__(self, driver):
    element = driver.find_element(*self.locator)   # Finding the referenced element
    if self.tag_value != element:
        return element
    else:
        return False

def wait_for_ajax(driver,tag):
    wait = WebDriverWait(driver, 30)
    try:
        wait.until(element_has_value((By.XPATH,"//div[@class='card ' and position()=1]//a" ), tag))
    except Exception as e:
        return Response(TimeoutException)

@api_view(["POST"])
@permission_classes([HasAPIKey])
def properties(request):
    properties_json={
        "status": True,
        "current_page":"",
        "page_count":""
    }
    try:
        key=request.META['HTTP_AUTHORIZATION']
        user_id = request.data['user_id']
        current_page = request.data['current_page']
        
        selenium = webdriver.Chrome(ChromeDriverManager().install())
        #selenium = webdriver.Chrome()
        url = f'https://app.earth2.io/#profile/{user_id}'
        
        selenium.get(url)
        
        timeout = 5
        try:
            element_present = EC.presence_of_element_located((By.XPATH, f"//ul[@class='pagination']//a[@data-argument={current_page}]"))
            WebDriverWait(selenium, timeout).until(element_present)
        except TimeoutException:
            print("Timed out waiting for page to load")
        selenium.find_element_by_xpath(f"//ul[@class='pagination']//a[@data-argument={current_page}]").click()
        
        tag = selenium.find_element_by_xpath("//div[@class='card ' and position()=1]//a")
        if current_page!=1:
            wait_for_ajax(selenium,tag)
        
        page_count=selenium.find_element_by_xpath("//ul[@class='pagination']//li[last()-1]").text.strip()
        html = selenium.page_source
        error,properties_list_json = scrape_properties(html)
        properties_json["data"]=properties_list_json
        properties_json["page_count"]=page_count
        properties_json["current_page"] = current_page
        if error:
            properties_json["status"]=False
            selenium.close()
            return Response(properties_json,status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        selenium.close()
        return Response( properties_json,status=status.HTTP_200_OK)
    except:
        properties_json["status"]=False
        properties_json["error"]="Something went wrong"
        selenium.close()
        return Response(properties_json,status=status.HTTP_504_GATEWAY_TIMEOUT)
        