# Caspio Data Page Processor

## Overview
The Caspio Data Page Processor is a Python-based automation tool designed to streamline the process of retrieving and processing data from Caspio datapages. It efficiently interacts with the Caspio database using both REST API calls and web scraping techniques, ultimately saving the extracted data to Excel and CSV files. 

## Features
- **Token-Based Authentication**: Securely connects to Caspio using OAuth for API requests.
- **Data Retrieval**: Fetches a list of datapages and their detailed information from Caspio.
- **Web Scraping**: Utilizes Selenium for extracting additional datapage details not available via the API.
- **Data Filtering**: Identifies and excludes already processed datapages to optimize performance.
- **Error Logging**: Captures and logs errors during datapage processing for review and troubleshooting.
- **Data Export**: Saves processed datapage information in both Excel and CSV formats.

## Requirements
- Python 3.x
- Selenium WebDriver
- Pandas
- Openpyxl (for Excel file handling)
- Requests
- Tqdm (for progress bar functionality)
- A valid Caspio account with necessary access rights

## Selenium WebDriver Installation
The Caspio Data Page Processor requires Selenium WebDriver for its operation. Below are the links to download the WebDriver for different operating systems:

### WebDriver Downloads
- **ChromeDriver for Windows, macOS, and Linux**: 
  - [Download ChromeDriver](https://chromedriver.storage.googleapis.com/index.html?path=114.0.5735.90/)
  - Ensure to download the version of ChromeDriver that matches your Chrome browser's version.

### Setting Up WebDriver
After downloading, extract the WebDriver and ensure it is placed in a directory included in your system's PATH. This will allow Selenium to access the WebDriver during the script execution. 

For more detailed instructions on setting up Selenium WebDriver, you can refer to the [Selenium documentation](https://www.selenium.dev/documentation/en/).

### Operating System Specific Notes
- **macOS Users**: You may need to update security permissions to allow the execution of the WebDriver. This can typically be done through the 'Security & Privacy' settings if a warning prompts upon first execution.
- **Linux Users**: Ensure that the WebDriver file has execution permissions. You can set this by running `chmod +x chromedriver` in the terminal where 'chromedriver' is the downloaded WebDriver file.

With the WebDriver set up correctly, you'll be able to run the Caspio Data Page Processor without any issues related to Selenium.

## Installation

```bash
pip install selenium pandas openpyxl requests tqdm
```

## Usage
- Update the CaspioAPI class with your Caspio client credentials (client_id and client_secret).
- Create an instance of CaspioDataPageProcessor with your Caspio account email, password, and the specific application name:
```bash
processor = CaspioDataPageProcessor("your_email@example.com", "your_password", "your_app_name")
```
- Call the run method to start the data processing:
```bash
processor.run()
```
```bash
processor.save_to_excel()
processor.save_to_csv()
processor.write_errors_to_file()
```
## Structure
- CaspioAPI: Handles API interactions with Caspio, including authentication and data retrieval.
- CaspioDataPageProcessor: Orchestrates the

## Error Handling and Logs
If any errors occur during the operation of the Caspio Data Page Processor, the script is designed to capture these issues and log them into a text file for later review and troubleshooting. This feature ensures that any problems encountered during the processing of datapages can be systematically addressed.

### Error Log File
- **File Name**: `errorLogsCaspioDataPageProcessor.txt`
- **Location**: The file is created in the current working directory of the script.
- **Content**: Contains detailed logs of any exceptions or errors encountered during the execution of the script.
- **Usage**: Review this log file to understand and rectify any issues that may have occurred. This is particularly useful for identifying and resolving problems in subsequent runs of the processor.

It is recommended to regularly check this log file if you're running the processor frequently or with large datasets. Timely identification and resolution of issues will ensure smoother operation and maintenance of your Caspio Data Page Processor.

