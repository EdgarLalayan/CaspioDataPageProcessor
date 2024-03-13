from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from requests.auth import HTTPBasicAuth
import requests
import logging
import pandas as pd
from openpyxl import Workbook
from datetime import datetime
from tqdm import tqdm
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CaspioAPI:
    def __init__(self):
        self.token = self.get_access_token()
        #print(self.token)
        self.base_url = "https://umnitech.caspio.com/rest/v2/"

    def get_access_token(self):
        client_id = 'bf6207b0e30245f5297065ad167fc1e81aaff466b96e883177'
        client_secret = 'fd4fc452821846869f97c9d3f719f01362c95425d938ca4e6a'
        token_url = 'https://c0abo866.caspio.com/oauth/token'

        data = {
            'grant_type': 'client_credentials'
        }

        try:
            response = requests.post(token_url, data=data, auth=HTTPBasicAuth(client_id, client_secret))

            if response.status_code == 200:
                logging.info("Access token successfully fetched.")
                return response.json().get('access_token')
            else:
                logging.error(f"Error fetching access token: {response.status_code} - {response.text}")
                print(f"Error fetching access token: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logging.exception("An error occurred while fetching the access token.")
            return None



    # Call the method to get applications
    # Pass an optional parameter 'app_name' if you want to filter applications by AppName
    def get_applications(self, app_name=None):
        # Endpoint URL
        url = self.base_url + "applications"

        # Headers
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            applications = response.json()["Result"]
            if app_name:
                filtered_applications = [app for app in applications if app["AppName"].lower().find(app_name.lower()) != -1]
                return filtered_applications
            else:
                return applications
        else:
            print("Error:", response.status_code)
            print("Response content:", response.text)
            return None
    

    def get_datapages_by_external_key(self, external_key=None, app_name=None):
        # If app_name is provided, get external_key using app_name
        if app_name and not external_key:
            applications = self.get_applications(app_name)
            if applications:
                external_key = applications[0]["ExternalKey"]
            else:
                print("No application found with the provided app_name.")
                return None
        
        # If external_key is provided, construct the URL
        if external_key:
            url = self.base_url + f"applications/{external_key}/datapages"
        else:
            print("Missing external_key parameter.")
            return None
            
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()['Result']
        else:
            print("Error:", response.status_code)
            print("Response content:", response.text)
            return None

    def get_table_data(self, table_name):
        url = f"{self.base_url}tables/{table_name}/records"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            logging.info("Data successfully fetched from table.")
            return response.json().get('Result')
        else:
            logging.error(f"Error fetching data from table: {response.status_code} - {response.text}")
            return None



class CaspioDataPageProcessor:
    def __init__(self, email, password, app_name):
        self.driver = self._initialize_driver()
        self._login(email, password)
        self.base_target_url = "https://umnitech.caspio.com/ui/search#"
        self.caspioAPI = CaspioAPI()
        self.allDataPagesInfo = []
        self.errorsDataPages = []

        # Fetch all datapages for the app
        self.datapages = self.caspioAPI.get_datapages_by_external_key(app_name=app_name)

        # Fetch the already processed datapages
        self.tableData = self.caspioAPI.get_table_data('Temp_Datapage_List_From_Bridge')

        # Extracting the list of already processed datapage app keys
        processed_datapage_keys = {datapage['Datapage_App_Key'] for datapage in self.tableData}

        # Filtering out the processed datapages
        self.datapages = [dp for dp in self.datapages if dp['AppKey'] not in processed_datapage_keys]
        logging.info(f"Number of unprocessed datapages: {len(self.datapages)}")


    def _initialize_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        driver = webdriver.Chrome(options=chrome_options)
        return driver

    def _login(self, email, password):
        login_url = "https://id.caspio.com/login"
        self.driver.get(login_url)
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "EmailField")))
            self.driver.find_element(By.ID, "EmailField").send_keys(email)
            self.driver.find_element(By.ID, "PasswordField").send_keys(password)
            self.driver.find_element(By.ID, "PasswordField").send_keys(Keys.RETURN)
            WebDriverWait(self.driver, 10).until(EC.url_contains("umnitech.caspio.com"))
        except TimeoutException as e:
            print(f"Login failed: {e}")
            self.driver.quit()
            exit()

    def _process_datapage(self, datapage, First=False):
        try:
            logging.info(f"Processing datapage: {datapage.get('AppKey')}")
            appkey = datapage.get('AppKey') 
            target_url = self.base_target_url + appkey
            
            self.driver.get(target_url)
            time.sleep(2)
            
            # Click on settings icon and apply configuration only for the first element
            if First:
                settings_icon = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.ID, "settings-icon")))
                settings_icon.click()

                # Find and click on the checkboxes
                checkboxes = ["checkCol3", "checkCol4", "checkCol8", "checkCol10"]
                for checkbox_id in checkboxes:
                    checkbox = self.driver.find_element(by='id', value=checkbox_id)
                    checkbox.click()

                # Find and click on the apply button
                apply_button = self.driver.find_element(by='id', value="applyConfColumnSettings")
                apply_button.click()

            def correct_xpath(xpath):
                parts = xpath.split('/')
                corrected = []
                div2_count = 0
                for part in parts:
                    if 'div[2]' in part:
                        div2_count += 1
                        if div2_count == 2:
                            continue
                    corrected.append(part)
                return '/'.join(corrected)

            # Original XPaths
            xpaths = {
                'deployed': '//*[@id="ListContent"]/div[2]/div/div[2]/div/div[8]/div',
                'data_source': '//*[@id="ListContent"]/div[2]/div/div[2]/div/div[3]/div',
                'authentication': '//*[@id="ListContent"]/div[2]/div/div[2]/div/div[6]/div',
                'style': '//*[@id="ListContent"]/div[2]/div/div[2]/div/div[4]/div',
                'localization': '//*[@id="ListContent"]/div[2]/div/div[2]/div/div[5]/div'
            }

            data_info = {}
            for key, xpath in xpaths.items():
                try:
                    element = self.driver.find_element(by='xpath', value=xpath)
                except NoSuchElementException:
                    # Correct the XPath and try again
                    corrected_xpath = correct_xpath(xpath)
                    element = self.driver.find_element(by='xpath', value=corrected_xpath)
                data_info[key] = element.text



            DataPageInfo = {
                'Datapage_App_Key': appkey,
                'App_Name': datapage.get('AppName'),
                'Folder': datapage.get('Path'),
                'Datapage_Name': datapage.get('Name'),
                'Datapage_Title': '',
                'Caspio_Bridge_Deployed_YN': data_info['deployed'], 
                'Data_Source': data_info['data_source'],
                'Authentication': data_info['authentication'],
                'Style': data_info['style'],
                'Localization': data_info['localization'],
                'Created_Date': datapage.get('DateCreated'), 
                'Created_By_Person_Name': datapage.get('CreatedBy'),
                'Last_Modified_Date': datapage.get('DateModified'), 
                'Last_Modified_By_Person_Name': datapage.get('ModifiedBy')
            }
            deployed = data_info['deployed']
            DataPageInfo['Caspio_Bridge_Deployed_YN'] = 'Y' if deployed == 'Enabled' else 'N' if deployed == 'Disabled' else deployed
            def format_date(date_str):
                try:
                    return datetime.strptime(date_str.split('T')[0], '%Y-%m-%d').strftime('%m/%d/%Y')
                except ValueError:
                    return date_str  

            DataPageInfo['Created_Date'] = format_date(datapage.get('DateCreated'))
            DataPageInfo['Last_Modified_Date'] = format_date(datapage.get('DateModified'))

            return DataPageInfo

        except Exception as e:
            logging.exception("An error occurred while processing a datapage.")
            return None


    def run(self):
        for i, datapage in tqdm(enumerate(self.datapages), total=len(self.datapages), desc="Processing datapages"):
            data_info = self._process_datapage(datapage, First=(i == 0))
            if data_info:
                self.allDataPagesInfo.append(data_info)
            else:
                self.errorsDataPages.append(datapage)
        self.driver.quit()

    def write_errors_to_file(self):
        with open('errorLogsCaspioDataPageProcessor.txt', 'w') as file:
            for error in self.errorsDataPages:
                file.write(str(error) + '\n')

    def save_to_excel(self):
        df = pd.DataFrame(self.allDataPagesInfo)
        with pd.ExcelWriter('allDataPagesInfo.xlsx', engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        print("Excel file created successfully.")
    def save_to_csv(self):
        df = pd.DataFrame(self.allDataPagesInfo)
        df.to_csv('allDataPagesInfo.csv', index=False)
        print("CSV file created successfully.")


if __name__ == "__main__":
    processor = CaspioDataPageProcessor("tkeal96@gmail.com", "Masivski96$", "WMV4")
    processor.run()
    if len(processor.errorsDataPages) > 0:
        processor.write_errors_to_file()
    processor.save_to_excel()
    processor.save_to_csv()











