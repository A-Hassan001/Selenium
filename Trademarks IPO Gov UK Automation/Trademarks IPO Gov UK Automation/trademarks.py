import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import os
import csv
import json
import winreg
import logging
from random import randint
from time import sleep, time
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from undetected_chromedriver import Chrome, ChromeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException


class Trademarks:
    # Create a custom logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    log_filename = f'logs/logs {datetime.now().strftime("%d%m%Y%H%M")}.txt'
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)

    # Create handlers
    console_handler = logging.StreamHandler()  # Console output_1
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')  # Log to a file

    # Set the log level for handlers
    console_handler.setLevel(logging.INFO)  # Console logs are less verbose
    file_handler.setLevel(logging.DEBUG)  # File logs capture everything

    # Create formatters and add them to the handlers
    formatter = logging.Formatter('%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    cookies = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger.info(f'\nScript started at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self.search_url = "https://trademarks.ipo.gov.uk/ipo-tmtext"

        self.config = self.read_json('config.json')
        input_file = f"input/{self.config.get('input_file_name')}"
        self.target_column_name = self.config.get('target_column_name')

        self.input_file = input_file
        self.input_companies = self.read_csv(input_file)

        self.output_folder = "output"
        os.makedirs(self.output_folder, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(input_file))[0]
        self.full_output_path = os.path.join(self.output_folder, f"{base_name}_(full_results).csv")
        self.no_tm_output_path = os.path.join(self.output_folder, f"{base_name}_(no_trademark_only).csv")
        self.processed_titles = self.load_existing_results()
        self.driver = self.create_driver()

    def start_processing(self):
        for index, row in enumerate(self.input_companies):
            company_name = row[self.target_column_name].strip()
            company_key = company_name.lower()

            if company_key in self.processed_titles:
                self.logger.info(f"Skipping already processed: {company_name}\n")
                continue

            self.logger.info("\n----------------------------------")
            self.logger.info(f"[{index + 1}/{len(self.input_companies)}] {company_name}")

            # Retry logic
            result = "error"

            for attempt in range(3):
                print(f"Attempt {attempt + 1} for {company_name}")
                result = self.search_trademark(company_name)

                if result in ["Yes", "No"]:
                    break

                print(f"Retrying {company_name}...")

                # Skip if still error after retries
                if result == "error":
                    print(f"Failed after 3 retries: {company_name}")
                    continue

            self.logger.info(f"Trademark Registered: {result}\n")

            row["uk_trademark_registered"] = result

            self.append_full_result(row)
            if result.lower() == "no":
                self.append_no_trademark(row)


    def search_trademark(self, company_name):
        input_keyword_selector = '[name="wordSearchPhrase"]'
        search_btn_selector = 'button#button'

        try:
            self.driver.get(self.search_url)
            sleep(5)

            self.is_element_exist(css_selector=input_keyword_selector, timeout=60)

            dropdown_selector = (By.NAME, "wordSearchType")

            if self.is_element_exist(css_selector="[name='wordSearchType']", timeout=10):
                dropdown_element = self.driver.find_element(*dropdown_selector)
                dropdown = Select(dropdown_element)

                dropdown.select_by_visible_text(f"{self.config.get('search_type', '')}")

            else:
                self.logger.error('Search type is rong.')
                return "error"


            if not self.is_element_exist(css_selector=input_keyword_selector, timeout=2):
                self.driver.refresh()
                sleep(randint(5,10))
                self.is_element_exist(css_selector=input_keyword_selector, timeout=60)

            if not self.is_element_exist(css_selector=input_keyword_selector, timeout=1):
                return "error"

            search_box = self.driver.find_element(By.CSS_SELECTOR, input_keyword_selector)

            search_box.clear()
            sleep(1)

            search_box.send_keys(company_name)
            sleep(2)

            search_btn = self.driver.find_element(By.CSS_SELECTOR, search_btn_selector)

            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_btn)
            sleep(1)

            search_btn.click()
            sleep(randint(2,6))

            self.wait_for_search_results()

            if self.is_element_exist(css_selector='.search-results .grid-row', timeout=2):
                return "Yes"

            # Arslan logic
            try:
                current_url = self.driver.current_url

                if "result" in current_url.lower():
                    return "Yes"

                else:
                    try:
                        errors = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.error-summary")))
                    except:
                        errors = []

                    if not errors:
                        try:
                            results = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located(
                                      (By.CSS_SELECTOR, ".form.search-form div.search-results")))
                        except:
                            results = []

                        if results:
                            return "Yes"

                    if errors:
                        error_box = errors[0]
                        li_elements = error_box.find_elements(By.CSS_SELECTOR, "ul.error-summary-list li")

                        if not li_elements:
                            return "Yes"

                        msg = li_elements[0].get_attribute("innerText").strip().lower()

                        if "no trade marks matching" in msg:
                            return "No"

                        if "more than 1,000 results" in msg:
                            return "Yes"

                        return "No"

                    return "No"

            except Exception:
                self.logger.info("Step 3 failed: result parsing issue\n")
                return "error"

        except Exception:
            self.logger.info(f"Fatal error checking '{company_name}'\n")

    def wait_for_search_results(self, max_minutes=5):
        start_time = time()
        max_duration = max_minutes * 60

        while True:
            # Stop loop after max time
            if time() - start_time > max_duration:
                self.logger.warning(f"Timeout: exceeded {max_minutes} minutes\n")
                return False

            # Results found
            if self.is_element_exist(css_selector='.search-results .grid-row', timeout=2):
                return True

            # No results message found
            if 'No trade marks matching your search criteria were found'.lower() in self.driver.page_source.lower():
                return False

            sleep(2)

    def append_full_result(self, row):
        """Append complete result row to full results CSV."""

        file_exists = os.path.exists(self.full_output_path)

        fieldnames = list(row.keys())

        if "uk_trademark_registered" not in fieldnames:
            fieldnames.append("uk_trademark_registered")

        with open(self.full_output_path, "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow(row)

    def append_no_trademark(self, row):
        """Append companies with NO trademark to separate CSV file."""

        file_exists = os.path.exists(self.no_tm_output_path)

        with open(self.no_tm_output_path, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            if not file_exists:
                writer.writerow(["companyName", "uk_trademark_registered"])

            writer.writerow([
                row.get(self.target_column_name, ""),
                row.get("uk_trademark_registered", "")
            ])

    def read_txt_file(self, filename):
        try:
            with open(filename, mode='r', encoding='utf-8') as txt_file:
                return [line.strip() for line in txt_file.readlines() if line.strip()]
        except:
            return []

    def create_driver(self):
        chrome_options = ChromeOptions()

        # Create local profile directory inside project
        profile_path = os.path.abspath("chrome_profile")
        os.makedirs(profile_path, exist_ok=True)

        chrome_options.add_argument(f"--user-data-dir={profile_path}")
        chrome_options.add_argument("--profile-directory=Default")

        # # Reduce automation detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        chrome_version = self.get_chrome_major_version()
        driver = Chrome(options=chrome_options, version_main=chrome_version)
        driver.maximize_window()
        return driver

    def get_chrome_major_version(self):
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Google\Chrome\BLBeacon"
            )
        except FileNotFoundError:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"Software\Google\Chrome\BLBeacon"
            )

        version, _ = winreg.QueryValueEx(key, "version")
        major_version = int(version.split('.')[0])
        return major_version

    def read_json_file(self):
        with open('input/config.json', mode='r', encoding='utf-8') as json_file:
            return json.load(json_file)

    def is_element_exist(self, css_selector='', xpath='', timeout=30):
        select_by = By.XPATH if xpath else By.CSS_SELECTOR
        selector = css_selector if css_selector else xpath

        try:
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(
                (select_by, selector)))

            return True

        except NoSuchElementException:
            return False

        except TimeoutException:
            return False

    def read_json(self, file_path):
        """ Read JSON configuration file."""

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)

        except Exception:
            return {}

    def load_existing_results(self):
        """ Load already processed company names from existing output_1 file."""

        processed = set()

        if os.path.exists(self.full_output_path):
            with open(self.full_output_path, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row in reader:
                    title = row.get(self.target_column_name)
                    if title:
                        processed.add(title.strip().lower())

        return processed

    def read_csv(self, file_name):
        """ Read input CSV file and return rows containing target column values."""

        rows = []

        with open(file_name, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            if self.target_column_name not in reader.fieldnames:
                raise Exception(f"CSV must contain '{self.target_column_name}' column")

            for row in reader:
                if row.get(self.target_column_name):
                    rows.append(row)

        return rows

if __name__ == '__main__':
    try:
        trademark_obj = Trademarks()
        trademark_obj.start_processing()

        trademark_obj.logger.info(f'\nScript closed at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        trademark_obj.driver.close()
        trademark_obj.driver.quit()

    except Exception as e:
        print(e)

    input('Press Any Key to close the window...')


