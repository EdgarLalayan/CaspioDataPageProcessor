from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains
import ast
import re
import time
from requests.auth import HTTPBasicAuth
import requests
import pandas as pd
from openpyxl import Workbook
from datetime import datetime
from tqdm import tqdm
import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class CaspioAPI:
    def __init__(self):
        self.token = self.get_access_token()
        # print(self.token)
        self.base_url = "https://umnitech.caspio.com/rest/v2/"

    def get_access_token(self):
        client_id = ''
        client_secret = ''
        token_url = 'https://c0abo866.caspio.com/oauth/token'

        data = {
            'grant_type': 'client_credentials'
        }

        try:
            response = requests.post(
                token_url, data=data, auth=HTTPBasicAuth(client_id, client_secret))

            if response.status_code == 200:
                logging.info("Access token successfully fetched.")
                return response.json().get('access_token')
            else:
                logging.error(
                    f"Error fetching access token: {response.status_code} - {response.text}")
                print(
                    f"Error fetching access token: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logging.exception(
                "An error occurred while fetching the access token.")
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
                filtered_applications = [
                    app for app in applications if app["AppName"].lower().find(app_name.lower()) != -1]
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
            logging.error(
                f"Error fetching data from table: {response.status_code} - {response.text}")
            return None

    def post(self, resource, resource_name, data):
        url = f"{self.base_url}{resource}/{resource_name}/records?response=rows"

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=data, headers=headers)

            if response.status_code == 200 or response.status_code == 201:
                logging.info("POST request successful.")
                return response.json().get('Result')[0] if response.json().get('Result') else None
            else:
                logging.error(
                    f"Error in POST request: {response.status_code} - {response.text}")
                print(
                    f"Error in POST request: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logging.exception("An error occurred in POST request.")
            return None

    def put(self, resource, resource_name, query, data_for_update):
        try:
            url = f"{self.base_url}{resource}/{resource_name}/records?response=rows&{query}"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            response = requests.put(url, json=data_for_update, headers=headers)

            if response.status_code in [200, 201]:
                logging.info(response.json())
                return response.json()
            else:
                logging.error(
                    f"Error in PUT request: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logging.exception("An error occurred in PUT request.")
            return None


class CaspioDataPageProcessor:
    def __init__(self, email, password, app_name):
        self.driver = self._initialize_driver()
        self._login(email, password)
        self.base_target_url = "https://umnitech.caspio.com/ui/search#"
        self.caspioAPI = CaspioAPI()
        self.allDataPagesInfo = []
        self.errorsDataPages = []

        self.datapages = self.caspioAPI.get_datapages_by_external_key(
            app_name=app_name)
        # Fetch the already processed datapages
        self.Tbl_WMV_Datapage_Definitions = self.caspioAPI.get_table_data(
            'WMV_Datapage_Definitions')
        self.tableDataTitle = self.caspioAPI.get_table_data(
            'WMV_Datapage_Definitions')

        logging.info(f"Number of  datapages: {len(self.datapages)}")

    def _initialize_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        driver = webdriver.Chrome(options=chrome_options)

        # Set zoom to 50%
        driver.execute_script("document.body.style.zoom='50%'")
        
        return driver

    def _login(self, email, password):
        login_url = "https://id.caspio.com/login"
        self.driver.get(login_url)
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "EmailField")))
            self.driver.find_element(By.ID, "EmailField").send_keys(email)
            self.driver.find_element(
                By.ID, "PasswordField").send_keys(password)
            self.driver.find_element(
                By.ID, "PasswordField").send_keys(Keys.RETURN)
            WebDriverWait(self.driver, 10).until(
                EC.url_contains("umnitech.caspio.com"))
        except TimeoutException as e:
            print(f"Login failed: {e}")
            self.driver.quit()
            exit()

    def _process_datapage(self, datapage, First=False):
        def find_last_used_date(data_array):
            most_recent_date = None
            most_recent_date_str = ""
            date_pattern = re.compile(r'(\d{2} \w{3} \d{4} \d{2}:\d{2} [AP]M)')

            for item in data_array:
                matches = date_pattern.findall(item)
                for date_str in matches:
                    try:
                        date = datetime.strptime(date_str, '%d %b %Y %I:%M %p')
                        if most_recent_date is None or date > most_recent_date:
                            most_recent_date = date
                            most_recent_date_str = date.strftime(
                                '%m/%d/%Y')  # Format date as MM/DD/YYYY
                    except ValueError:
                        continue

            return most_recent_date_str if most_recent_date_str else None

        def find_title_by_app_key(app_key):
            for row in self.tableDataTitle:
                if row['Caspio_App_Key'] == app_key:
                    return row.get('Title', '')
            return None

        try:
            logging.info(f"Processing datapage: {datapage.get('AppKey')}")
            appkey = datapage.get('AppKey')
            datapage_title = find_title_by_app_key(appkey)

            target_url = self.base_target_url + appkey

            self.driver.get(target_url)
            time.sleep(2)

            # Click on settings icon and apply configuration only for the first element
            if First:
                settings_icon = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "settings-icon")))
                settings_icon.click()

                checkboxes = ["checkCol3", "checkCol4",
                              "checkCol8", "checkCol10"]
                for checkbox_id in checkboxes:
                    checkbox = self.driver.find_element(
                        by='id', value=checkbox_id)
                    checkbox.click()

                apply_button = self.driver.find_element(
                    by='id', value="applyConfColumnSettings")
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
                    element = self.driver.find_element(
                        by='xpath', value=corrected_xpath)
                data_info[key] = element.text

            name_links = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_all_elements_located((By.CLASS_NAME, "NameLink"))
            )
            if len(name_links) >= 2:
                name_link = name_links[1]
            else:
                name_link = name_links[0]
            # Move cursor to "NameLink" element
            ActionChains(self.driver).move_to_element(name_link).perform()

            properties_link = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//div[@class='Menu']/a[contains(text(), 'Properties')]"))
            )
            properties_link.click()

            try:
                show_more_button = WebDriverWait(self.driver, 3).until(
                    EC.visibility_of_element_located(
                        (By.CLASS_NAME, "ShowMore"))
                )
                show_more_button.click()
            except TimeoutException:
                logging.info(
                    "No 'Show More' button found or it took too long to appear.")
            except NoSuchElementException:
                # If 'Show More' button is absent
                logging.info("No 'Show More' button found.")

            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME, "RowProperties"))
            )

            lines = self.driver.find_elements(
                By.XPATH, "//div[@class='RowProperties Show']/div[@class='Content']/div[@class='Line']")

            host_pages_line = lines[-4] if len(lines) >= 4 else None
            if host_pages_line:
                data_elements = host_pages_line.find_elements(
                    By.XPATH, ".//div")
                data_array = [
                    element.text for element in data_elements if element.text != 'less...']
                last_used_date = find_last_used_date(data_array)

            DataPageInfo = {
                'Channel_KW': 'UNIVERSAL',
                'Active_YN': '1',
                'Caspio_App_Key': appkey,
                'App_Name': datapage.get('AppName'),
                'Path': datapage.get('Path'),
                'Name': datapage.get('Name'),
                #'Datapage_Title': datapage_title,
                'Deployed_YN': data_info['deployed'],
                'Data_Source': data_info['data_source'],
                'Authentication': data_info['authentication'],
                'Style': data_info['style'],#
                'Localization': data_info['localization'],
                'Last_Used_Date': last_used_date,
                'Created_Date': datapage.get('DateCreated'),
                'Created_By_Person_Name': datapage.get('CreatedBy'),
                'Last_Modified_Date': datapage.get('DateModified'),
                'Last_Modified_By_Person_Name': datapage.get('ModifiedBy')
            }

            deployed = data_info['deployed']
            DataPageInfo['Caspio_Bridge_Deployed_YN'] = '1' if deployed == 'Enabled' else '0' if deployed == 'Disabled' else deployed

            def format_date(date_str):
                try:
                    return datetime.strptime(date_str.split('T')[0], '%Y-%m-%d').strftime('%m/%d/%Y')
                except ValueError:
                    return None

            DataPageInfo['Datapage_Created_Date'] = format_date(
                datapage.get('DateCreated'))
            DataPageInfo['Last_Modified_Date'] = format_date(
                datapage.get('DateModified'))

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
        self._retry_errors()
        self.driver.quit()
        self._postToCaspioTable()

    def _postToCaspioTable(self):

        for datapage_info in tqdm(self.allDataPagesInfo, desc="Processing datapages"):
            # Check if the row already exists in Tbl_WMV_Datapage_Definitions
            existing_row = next(
                (row for row in self.Tbl_WMV_Datapage_Definitions if row['Caspio_App_Key'] == datapage_info['Caspio_App_Key']), None)

            if existing_row:
                # Compare existing row with new data to decide whether to update
                if self._is_data_different(existing_row, datapage_info):
                    response = self.caspioAPI.put('tables', 'WMV_Datapage_Definitions',
                                                  f"q.where=Caspio_App_Key='{datapage_info['Caspio_App_Key']}'", datapage_info)
                    if response:
                        logging.info(f"Data successfully updated: {response}")
                    else:
                        logging.error("Error in updating data")
                        self.errorsDataPages.append(datapage_info)
            else:
                # Use POST request for new data
                response = self.caspioAPI.post(
                    'tables', 'WMV_Datapage_Definitions', datapage_info)
                if response:
                    logging.info(f"Data successfully posted: {response}")
                else:
                    logging.error("Error in posting data")
                    self.errorsDataPages.append(datapage_info)

    def _is_data_different(self, existing_row, new_data):


        fields_to_compare = [
            'Channel_KW', 'Active_YN', 'Caspio_App_Key', 'App_Name',
            'Path', 'Name',  'Deployed_YN',
            'Data_Source', 'Authentication', 'Style', 'Localization',
            'Last_Used_Date', 'Created_Date', 'Created_By_Person_Name',
            'Last_Modified_Date', 'Last_Modified_By_Person_Name'
        ]

        for field in fields_to_compare:
            if existing_row.get(field) != new_data.get(field):
                return True

        return False

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

    def _retry_errors(self, errorLogsCaspioDataPageProcessor=False):
        successfully_processed = []

        if errorLogsCaspioDataPageProcessor:
            # Read error logs and parse into datapages
            with open('errorLogsCaspioDataPageProcessor.txt', 'r') as file:
                retry_list = [ast.literal_eval(line) for line in file]
        elif len(self.errorsDataPages) > 0:
            logging.info(
                f"Retrying {len(self.errorsDataPages)} errored datapages...")
            retry_list = self.errorsDataPages
            self.errorsDataPages = []
        else:
            return  # Nothing to retry

        # Process each errored datapage again
        for i, datapage in tqdm(enumerate(retry_list), total=len(retry_list), desc="Retrying errored datapages"):
            data_info = self._process_datapage(datapage, First=(i == 0))
            if data_info:
                self.allDataPagesInfo.append(data_info)
                successfully_processed.append(datapage)
            else:
                self.errorsDataPages.append(datapage)

        # Update the database
        self._postToCaspioTable()

        # Update the error log file
        if errorLogsCaspioDataPageProcessor:
            self._update_error_log(successfully_processed)

    def _update_error_log(self, successfully_processed):
        with open('errorLogsCaspioDataPageProcessor.txt', 'r') as file:
            current_errors = [ast.literal_eval(line) for line in file]
        # Filter out successfully processed datapages
        updated_errors = [
            error for error in current_errors if error not in successfully_processed]
        with open('errorLogsCaspioDataPageProcessor.txt', 'w') as file:
            for error in updated_errors:
                file.write(str(error) + '\n')


if __name__ == "__main__":
    processor = CaspioDataPageProcessor(
        "Login", "Password", "WorkMovr 4") 
    processor.run()
    processor._retry_errors(errorLogsCaspioDataPageProcessor=True)

    if len(processor.errorsDataPages) > 0:
        processor.write_errors_to_file()

    # processor.save_to_excel()
    # processor.save_to_csv()
