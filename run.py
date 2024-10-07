# Imports
import os
import csv
import re
import pyautogui
pyautogui.FAILSAFE = False
from random import choice, shuffle, randint
from datetime import datetime
from modules.open_chrome import *
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, NoSuchWindowException, ElementNotInteractableException
from config.profile import *
from config.questions import *
from config.search import *
from config.creds import *
from config.settings import *
from modules.browser_launcher import *
from modules.actions import *
from modules.input_validator import validate_config
from typing import Literal

if run_in_background:
    pause_at_failed_question = pause_before_submit = run_non_stop = False

first_name = first_name.strip()
middle_name = middle_name.strip()
last_name = last_name.strip()
full_name = f"{first_name} {middle_name} {last_name}".strip() if middle_name else f"{first_name} {last_name}"

useNewResume = True
randomly_answered_questions = set()

tabs_count = 1
easy_applied_count = 0
external_jobs_count = 0
failed_count = 0
skip_count = 0
dailyEasyApplyLimitReached = False

re_experience = re.compile(r'[(]?\s*(\d+)\s*[)]?\s*[-to]*\s*\d*[+]*\s*year[s]?', re.IGNORECASE)

desired_salary_lakhs = str(round(desired_salary / 100000, 2))
desired_salary_monthly = str(round(desired_salary/12, 2))
desired_salary = str(desired_salary)

current_ctc_lakhs = str(round(current_ctc / 100000, 2))
current_ctc_monthly = str(round(current_ctc/12, 2))
current_ctc = str(current_ctc)

notice_period_months = str(notice_period//30)
notice_period_weeks = str(notice_period//7)
notice_period = str(notice_period)

# Check if the user is logged in on LinkedIn
def is_logged_in_LN() -> bool:
    if driver.current_url == "https://www.linkedin.com/feed/": 
        return True
    if try_linkText(driver, "Sign in") or try_xp(driver, '//button[@type="submit" and contains(text(), "Sign in")]') or try_linkText(driver, "Join now"):
        return False
    print_lg("Didn't find Sign in link, assuming user is logged in!")
    return True

def login_LN() -> None:
    # Attempt to log in to LinkedIn
    driver.get("https://www.linkedin.com/login")
    try:
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Forgot password?")))
        try:
            text_input_by_ID(driver, "username", username, 1)
        except Exception:
            print_lg("Couldn't find username field.")
        try:
            text_input_by_ID(driver, "password", password, 1)
        except Exception:
            print_lg("Couldn't find password field.")
        driver.find_element(By.XPATH, '//button[@type="submit" and contains(text(), "Sign in")]').click()
    except Exception:
        try:
            find_by_class(driver, "profile__details").click()
        except Exception:
            print_lg("Couldn't Login!")

    try:
        wait.until(EC.url_to_be("https://www.linkedin.com/feed/"))
        print_lg("Login successful!")
    except Exception:
        print_lg("Login attempt failed! Try logging in manually.")
        manual_login_retry(is_logged_in_LN, 2)

def get_applied_job_ids() -> set:
    # Get a set of applied job IDs from the CSV file
    job_ids = set()
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            job_ids = {row[0] for row in csv.reader(file)}
    except FileNotFoundError:
        print_lg(f"The CSV file '{file_name}' does not exist.")
    return job_ids

def set_search_location() -> None:
    location = search_location.strip()
    if location:
        try:
            print_lg(f'Setting search location as: "{location}"')
            search_location_ele = try_xp(driver, ".//input[@aria-label='City, state, or zip code' and not(@disabled)]", False)
            text_input(actions, search_location_ele, location, "Search Location")
        except ElementNotInteractableException:
            actions.send_keys(Keys.TAB * 2).perform()
            actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
            actions.send_keys(location).perform()
            sleep(2)
            actions.send_keys(Keys.ENTER).perform()
            try_xp(driver, ".//button[@aria-label='Cancel']")
        except Exception:
            try_xp(driver, ".//button[@aria-label='Cancel']")
            print_lg("Failed to update search location, continuing with default location!")


def apply_filters() -> None:
    set_search_location()
    
    try:
        recommended_wait = max(1 - click_gap, 0)  # Simplified wait logic

        # Apply filters
        wait.until(EC.presence_of_element_located((By.XPATH, '//button[normalize-space()="All filters"]'))).click()
        buffer(recommended_wait)

        filter_groups = [sort_by, date_posted, experience_level, companies, job_type, on_site, location, industry, job_function, job_titles, salary, benefits, commitments]
        for group in filter_groups:
            if group:
                multi_sel(driver, group) if group in [experience_level, job_type, on_site, salary, benefits, commitments] else multi_sel_noWait(driver, group, actions)
                buffer(recommended_wait)

        # Boolean button clicks
        boolean_filters = [(easy_apply_only, "Easy Apply"), (under_10_applicants, "Under 10 applicants"), 
                           (in_your_network, "In your network"), (fair_chance_employer, "Fair Chance Employer")]
        for condition, label in boolean_filters:
            if condition:
                boolean_button_click(driver, actions, label)

        # Apply the filtered results
        driver.find_element(By.XPATH, '//button[contains(@aria-label, "Apply current filters to show")]').click()

    except Exception:
        print_lg("Setting the preferences failed!")

def get_page_info() -> tuple[WebElement | None, int | None]:
    try:
        pagination_element = try_find_by_classes(driver, ["artdeco-pagination", "artdeco-pagination__pages"])
        scroll_to_view(driver, pagination_element)
        current_page = int(pagination_element.find_element(By.XPATH, "//li[contains(@class, 'active')]").text)
    except Exception:
        print_lg("Failed to find Pagination element, couldn't scroll to the end.")
        pagination_element, current_page = None, None
    return pagination_element, current_page


def get_job_main_details(job: WebElement, blacklisted_companies: set, rejected_jobs: set) -> tuple[str, str, str, str, str, bool]:
    # Get job details and return a tuple of job attributes
    job_details_button = job.find_element(By.CLASS_NAME, "job-card-list__title")
    scroll_to_view(driver, job_details_button, True)
    
    title = job_details_button.text
    company = job.find_element(By.CLASS_NAME, "job-card-container__primary-description").text
    job_id = job.get_dom_attribute('data-occludable-job-id')
    
    work_location_element = job.find_element(By.CLASS_NAME, "job-card-container__metadata-item").text
    work_style = work_location_element[work_location_element.rfind('(') + 1 : work_location_element.rfind(')')]
    work_location = work_location_element[:work_location_element.rfind('(')].strip()
    
    # Initialize skip flag based on blacklist or already applied jobs
    skip = False
    if company in blacklisted_companies:
        print_lg(f'Skipping "{title} | {company}" job (Blacklisted Company). Job ID: {job_id}!')
        skip = True
    elif job_id in rejected_jobs:
        print_lg(f'Skipping previously rejected "{title} | {company}" job. Job ID: {job_id}!')
        skip = True

    # Check if already applied
    try:
        if job.find_element(By.CLASS_NAME, "job-card-container__footer-job-state").text == "Applied":
            print_lg(f'Already applied to "{title} | {company}" job. Job ID: {job_id}!')
            skip = True
    except Exception:
        pass

    # Attempt to click the job details button if not skipped
    if not skip:
        try:
            job_details_button.click()
        except Exception:
            print_lg(f'Failed to click "{title} | {company}" job details button. Job ID: {job_id}!')
            discard_job()  # Handle the failure by discarding the job
            job_details_button.click()  # Retry clicking

    buffer(click_gap)
    
    return job_id, title, company, work_location, work_style, skip

# Function to check for Blacklisted words in About Company
def check_blacklist(rejected_jobs: set, job_id: str, company: str, blacklisted_companies: set) -> tuple[set, set, WebElement] | ValueError:
    jobs_top_card = try_find_by_classes(driver, [
        "job-details-jobs-unified-top-card__primary-description-container",
        "job-details-jobs-unified-top-card__primary-description",
        "jobs-unified-top-card__primary-description",
        "jobs-details__main-content"
    ])

    about_company_org = find_by_class(driver, "jobs-company__box")
    scroll_to_view(driver, about_company_org)
    about_company = about_company_org.text.lower()

    # Check for good words and skip blacklist check if found
    if any(word.lower() in about_company for word in about_company_good_words):
        print_lg(f'Found a good word, skipping blacklist check.')
    else:
        # Check for bad words and update blacklist if found
        for word in about_company_bad_words:
            if word.lower() in about_company:
                rejected_jobs.add(job_id)
                blacklisted_companies.add(company)
                raise ValueError(f'\n"{about_company_org}"\n\nContains "{word}".')

    buffer(click_gap)
    scroll_to_view(driver, jobs_top_card)
    return rejected_jobs, blacklisted_companies, jobs_top_card

def extract_years_of_experience(text: str) -> int:
    # Extract experience patterns like '10+ years', '5 years', '3-5 years', etc.
    matches = re.findall(re_experience, text)
    
    if not matches:
        print_lg(f'\n{text}\n\nCouldn\'t find experience requirement in About the Job!')
        return 0

    # Filter and return the maximum valid experience (up to 12 years)
    return max((int(match) for match in matches if int(match) <= 12), default=0)

# Function to upload resume
def upload_resume(modal: WebElement, resume: str) -> tuple[bool, str]:
    try:
        modal.find_element(By.NAME, "file").send_keys(os.path.abspath(resume))
        return True, os.path.basename(resume)
    except Exception:
        return False, "Previous resume"

# Function to answer common questions for Easy Apply
def answer_common_questions(label: str, answer: str) -> str:
    # Automatically set answer if the question relates to sponsorship or visa
    if 'sponsorship' in label.lower() or 'visa' in label.lower():
        return require_visa
    return answer

# Function to answer the questions for Easy Apply
def answer_questions(questions_list: set, work_location: str) -> set:
    # Get all questions from the page
    all_questions = driver.find_elements(By.CLASS_NAME, "jobs-easy-apply-form-element")

    for Question in all_questions:
        # Check if it's a select Question
        select = try_xp(Question, ".//select", False)
        if select:
            label_org = "Unknown"
            try:
                label = Question.find_element(By.TAG_NAME, "label")
                label_org = label.find_element(By.TAG_NAME, "span").text
            except: pass
            answer = 'Yes'
            label = label_org.lower()
            select = Select(select)
            selected_option = select.first_selected_option.text
            optionsText = []
            options = '"List of phone country codes"'
            if label != "phone country code":
                optionsText = [option.text for option in select.options]
                options = "".join([f' "{option}",' for option in optionsText])
            prev_answer = selected_option
            if overwrite_previous_answers or selected_option == "Select an option":
                if 'email' in label or 'phone' in label: answer = prev_answer
                elif 'gender' in label or 'sex' in label: answer = gender
                elif 'disability' in label: answer = disability_status
                elif 'proficiency' in label: answer = 'Professional'
                else: answer = answer_common_questions(label,answer)
                try: select.select_by_visible_text(answer)
                except NoSuchElementException as e:
                    possible_answer_phrases = ["Decline", "not wish", "don't wish", "Prefer not", "not want"] if answer == 'Decline' else [answer]
                    foundOption = False
                    for phrase in possible_answer_phrases:
                        for option in optionsText:
                            if phrase in option:
                                select.select_by_visible_text(option)
                                answer = f'Decline ({option})' if len(possible_answer_phrases) > 1 else option
                                foundOption = True
                                break
                        if foundOption: break
                    if not foundOption:
                        print_lg(f'Failed to find an option with text "{answer}" for question labelled "{label_org}", answering randomly!')
                        select.select_by_index(randint(1, len(select.options)-1))
                        answer = select.first_selected_option.text
                        randomly_answered_questions.add((f'{label_org} [ {options} ]',"select"))
            questions_list.add((f'{label_org} [ {options} ]', answer, "select", prev_answer))
            continue
        
        # Check if it's a radio Question
        radio = try_xp(Question, './/fieldset[@data-test-form-builder-radio-button-form-component="true"]', False)
        if radio:
            prev_answer = None
            label = try_xp(radio, './/span[@data-test-form-builder-radio-button-form-component__title]', False)
            try: label = find_by_class(label, "visually-hidden", 2.0)
            except: pass
            label_org = label.text if label else "Unknown"
            answer = 'Yes'
            label = label_org.lower()

            label_org += ' [ '
            options = radio.find_elements(By.TAG_NAME, 'input')
            options_labels = []
            
            for option in options:
                id = option.get_attribute("id")
                option_label = try_xp(radio, f'.//label[@for="{id}"]', False)
                options_labels.append( f'"{option_label.text if option_label else "Unknown"}"<{option.get_attribute("value")}>' ) # Saving option as "label <value>"
                if option.is_selected(): prev_answer = options_labels[-1]
                label_org += f' {options_labels[-1]},'

            if overwrite_previous_answers or prev_answer is None:
                if 'citizenship' in label or 'employment eligibility' in label: answer = us_citizenship
                elif 'veteran' in label or 'protected' in label: answer = veteran_status
                elif 'disability' in label or 'handicapped' in label: 
                    answer = disability_status
                else: answer = answer_common_questions(label,answer)
                foundOption = try_xp(radio, f".//label[normalize-space()='{answer}']", False)
                if foundOption: 
                    actions.move_to_element(foundOption).click().perform()
                else:    
                    possible_answer_phrases = ["Decline", "not wish", "don't wish", "Prefer not", "not want"] if answer == 'Decline' else [answer]
                    ele = options[0]
                    answer = options_labels[0]
                    for phrase in possible_answer_phrases:
                        for i, option_label in enumerate(options_labels):
                            if phrase in option_label:
                                foundOption = options[i]
                                ele = foundOption
                                answer = f'Decline ({option_label})' if len(possible_answer_phrases) > 1 else option_label
                                break
                        if foundOption: break
                    actions.move_to_element(ele).click().perform()
                    if not foundOption: randomly_answered_questions.add((f'{label_org} ]',"radio"))
            else: answer = prev_answer
            questions_list.add((label_org+" ]", answer, "radio", prev_answer))
            continue
        
        # Check if it's a text question
        text = try_xp(Question, ".//input[@type='text']", False)
        if text: 
            do_actions = False
            label = try_xp(Question, ".//label[@for]", False)
            try: label = label.find_element(By.CLASS_NAME,'visually-hidden')
            except: pass
            label_org = label.text if label else "Unknown"
            answer = "" # years_of_experience
            label = label_org.lower()

            prev_answer = text.get_attribute("value")
            if not prev_answer or overwrite_previous_answers:
                if 'experience' in label or 'years' in label: answer = years_of_experience
                elif 'phone' in label or 'mobile' in label: answer = phone_number
                elif 'street' in label: answer = street
                elif 'city' in label or 'location' in label or 'address' in label:
                    answer = current_city if current_city else work_location
                    do_actions = True
                elif 'signature' in label: answer = full_name # 'signature' in label or 'legal name' in label or 'your name' in label or 'full name' in label: answer = full_name     # What if question is 'name of the city or university you attend, name of referral etc?'
                elif 'name' in label:
                    if 'full' in label: answer = full_name
                    elif 'first' in label and 'last' not in label: answer = first_name
                    elif 'middle' in label and 'last' not in label: answer = middle_name
                    elif 'last' in label and 'first' not in label: answer = last_name
                    elif 'employer' in label: answer = recent_employer
                    else: answer = full_name
                elif 'notice' in label:
                    if 'month' in label:
                        answer = notice_period_months
                    elif 'week' in label:
                        answer = notice_period_weeks
                    else: answer = notice_period
                elif 'salary' in label or 'compensation' in label or 'ctc' in label or 'pay' in label: 
                    if 'current' in label or 'present' in label:
                        if 'month' in label:
                            answer = current_ctc_monthly
                        elif 'lakh' in label:
                            answer = current_ctc_lakhs
                        else:
                            answer = current_ctc
                    else:
                        if 'month' in label:
                            answer = desired_salary_monthly
                        elif 'lakh' in label:
                            answer = desired_salary_lakhs
                        else:
                            answer = desired_salary
                elif 'linkedin' in label: answer = linkedIn
                elif 'website' in label or 'blog' in label or 'portfolio' in label or 'link' in label: answer = website
                elif 'scale of 1-10' in label: answer = confidence_level
                elif 'headline' in label: answer = headline
                elif ('hear' in label or 'come across' in label) and 'this' in label and ('job' in label or 'position' in label): answer = "https://github.com/GodsScion/Auto_job_applier_linkedIn"
                elif 'state' in label or 'province' in label: answer = state
                elif 'zip' in label or 'postal' in label or 'code' in label: answer = zipcode
                elif 'country' in label: answer = country
                else: answer = answer_common_questions(label,answer)
                if answer == "":
                    randomly_answered_questions.add((label_org, "text"))
                    answer = years_of_experience
                text.clear()
                text.send_keys(answer)
                if do_actions:
                    sleep(2)
                    actions.send_keys(Keys.ARROW_DOWN)
                    actions.send_keys(Keys.ENTER).perform()
            questions_list.add((label, text.get_attribute("value"), "text", prev_answer))
            continue

        # Check if it's a textarea question
        text_area = try_xp(Question, ".//textarea", False)
        if text_area:
            label = try_xp(Question, ".//label[@for]", False)
            label_org = label.text if label else "Unknown"
            label = label_org.lower()
            answer = ""
            prev_answer = text_area.get_attribute("value")
            if not prev_answer or overwrite_previous_answers:
                if 'summary' in label: answer = summary
                elif 'cover' in label: answer = cover_letter
                text_area.clear()
                text_area.send_keys(answer)
                if answer == "": 
                    randomly_answered_questions.add((label_org, "textarea"))
            questions_list.add((label, text_area.get_attribute("value"), "textarea", prev_answer))
            continue

        # Check if it's a checkbox question
        checkbox = try_xp(Question, ".//input[@type='checkbox']", False)
        if checkbox:
            label = try_xp(Question, ".//span[@class='visually-hidden']", False)
            label_org = label.text if label else "Unknown"
            label = label_org.lower()
            answer = try_xp(Question, ".//label[@for]", False)  # Sometimes multiple checkboxes are given for 1 question, Not accounted for that yet
            answer = answer.text if answer else "Unknown"
            prev_answer = checkbox.is_selected()
            checked = prev_answer
            if not prev_answer:
                try:
                    actions.move_to_element(checkbox).click().perform()
                    checked = True
                except Exception as e: 
                    print_lg("Checkbox click failed!", e)
                    continue
            questions_list.add((f'{label} ([X] {answer})', checked, "checkbox", prev_answer))
            continue


    # Select todays date
    try_xp(driver, "//button[contains(@aria-label, 'This is today')]")

    # Collect important skills
    # if 'do you have' in label and 'experience' in label and ' in ' in label -> Get word (skill) after ' in ' from label
    # if 'how many years of experience do you have in ' in label -> Get word (skill) after ' in '

    return questions_list

def external_apply(pagination_element: WebElement, job_id: str, job_link: str, resume: str, date_listed, application_link: str, screenshot_name: str) -> tuple[bool, str, int]:
    global tabs_count, dailyEasyApplyLimitReached

    if easy_apply_only:
        try:
            if "exceeded the daily application limit" in driver.find_element(By.CLASS_NAME, "artdeco-inline-feedback__message").text:
                dailyEasyApplyLimitReached = True
        except Exception:
            pass
        print_lg("Easy apply failed!")
        return (True, application_link, tabs_count) if pagination_element else (False, application_link, tabs_count)

    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(span, "Apply") and not(span[contains(@class, "disabled")])]'))).click()
        driver.switch_to.window(driver.window_handles[-1])
        application_link = driver.current_url
        print_lg(f'Got the external application link "{application_link}"')
        if close_tabs: driver.close()
        driver.switch_to.window(linkedIn_tab)
        return False, application_link, len(driver.window_handles)

    except Exception as e:
        print_lg("Failed to apply!")
        failed_job(job_id, job_link, resume, date_listed, "Couldn't find Apply button or unable to switch tabs.", e, application_link, screenshot_name)
        global failed_count
        failed_count += 1
        return True, application_link, tabs_count

def failed_job(job_id: str, job_link: str, resume: str, date_listed, error: str, exception: Exception, application_link: str, screenshot_name: str) -> None:
    # Log failed job attempts
    try:
        with open(failed_file_name, 'a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=[
                'Job ID', 'Job Link', 'Resume Tried', 'Date listed', 'Date Tried', 
                'Assumed Reason', 'Stack Trace', 'External Job link', 'Screenshot Name'
            ])
            if file.tell() == 0: writer.writeheader()
            writer.writerow({
                'Job ID': job_id, 'Job Link': job_link, 'Resume Tried': resume, 
                'Date listed': date_listed, 'Date Tried': datetime.now(), 
                'Assumed Reason': error, 'Stack Trace': exception, 
                'External Job link': application_link, 'Screenshot Name': screenshot_name
            })
    except Exception as e:
        print_lg("Failed to update failed jobs list!", e)
        pyautogui.alert("Failed to log failed jobs. Check if the file is open or permission denied.", "Failed Logging")

def screenshot(driver: WebDriver, job_id: str, failedAt: str) -> str:
    # Capture a screenshot for debugging
    screenshot_name = f"{job_id} - {failedAt} - {datetime.now()}.png".replace(":", ".")
    path = f"{logs_folder_path}/screenshots/{screenshot_name}".replace("//", "/")
    driver.save_screenshot(path)
    return screenshot_name

def submitted_jobs(
    job_id: str, title: str, company: str, work_location: str, work_style: str, 
    description: str, experience_required: int | Literal['Unknown', 'Error in extraction'], 
    skills: list[str] | Literal['In Development'], hr_name: str | Literal['Unknown'], 
    hr_link: str | Literal['Unknown'], resume: str, reposted: bool, 
    date_listed: datetime | Literal['Unknown'], date_applied: datetime | Literal['Pending'], 
    job_link: str, application_link: str, questions_list: set | None, 
    connect_request: Literal['In Development']
) -> None:
    # Update the Applied Jobs CSV file after successful submission
    try:
        with open(file_name, mode='a', newline='', encoding='utf-8') as csv_file:
            fieldnames = [
                'Job ID', 'Title', 'Company', 'Work Location', 'Work Style', 'About Job', 
                'Experience required', 'Skills required', 'HR Name', 'HR Link', 'Resume', 
                'Re-posted', 'Date Posted', 'Date Applied', 'Job Link', 'External Job link', 
                'Questions Found', 'Connect Request'
            ]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            if csv_file.tell() == 0:
                writer.writeheader()
            writer.writerow({
                'Job ID': job_id, 'Title': title, 'Company': company, 
                'Work Location': work_location, 'Work Style': work_style, 
                'About Job': description, 'Experience required': experience_required, 
                'Skills required': skills, 'HR Name': hr_name, 'HR Link': hr_link, 
                'Resume': resume, 'Re-posted': reposted, 'Date Posted': date_listed, 
                'Date Applied': date_applied, 'Job Link': job_link, 
                'External Job link': application_link, 'Questions Found': questions_list, 
                'Connect Request': connect_request
            })
    except Exception as e:
        print_lg("Failed to update submitted jobs list!", e)
        pyautogui.alert(
            "Failed to update the applied jobs file!\n"
            "Possible reasons:\n1. File is open by another program\n"
            "2. Permission denied\n3. File not found", "Failed Logging"
        )

def discard_job() -> None:
    # Discard the job application by sending ESC and clicking 'Discard'
    actions.send_keys(Keys.ESCAPE).perform()
    wait_span_click(driver, 'Discard', 2)

# Function to apply to jobs
def apply_to_jobs(search_terms: list[str]) -> None:
    applied_jobs = get_applied_job_ids()
    rejected_jobs = set()
    blacklisted_companies = set()
    global current_city, failed_count, skip_count, easy_applied_count, external_jobs_count, tabs_count, pause_before_submit, pause_at_failed_question, useNewResume
    current_city = current_city.strip()

    if randomize_search_order:  shuffle(search_terms)
    for searchTerm in search_terms:
        driver.get(f"https://www.linkedin.com/jobs/search/?keywords={searchTerm}")
        print_lg("\n________________________________________________________________________________________________________________________\n")
        print_lg(f'\n>>>> Now searching for "{searchTerm}" <<<<\n\n')

        apply_filters()

        current_count = 0
        try:
            while current_count < switch_number:
                # Wait until job listings are loaded
                wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li[contains(@class, 'jobs-search-results__list-item')]")))

                pagination_element, current_page = get_page_info()

                # Find all job listings in current page
                buffer(3)
                job_listings = driver.find_elements(By.CLASS_NAME, "jobs-search-results__list-item")  

            
                for job in job_listings:
                    if keep_screen_awake: pyautogui.press('shiftright')
                    if current_count >= switch_number: break
                    print_lg("\n-@-\n")

                    job_id,title,company,work_location,work_style,skip = get_job_main_details(job, blacklisted_companies, rejected_jobs)
                    
                    if skip: continue
                    # Redundant fail safe check for applied jobs!
                    try:
                        if job_id in applied_jobs or find_by_class(driver, "jobs-s-apply__application-link", 2):
                            print_lg(f'Already applied to "{title} | {company}" job. Job ID: {job_id}!')
                            continue
                    except Exception as e:
                        print_lg(f'Trying to Apply to "{title} | {company}" job. Job ID: {job_id}')

                    job_link = "https://www.linkedin.com/jobs/view/"+job_id
                    application_link = "Easy Applied"
                    date_applied = "Pending"
                    hr_link = "Unknown"
                    hr_name = "Unknown"
                    connect_request = "In Development" # Still in development
                    date_listed = "Unknown"
                    description = "Unknown"
                    experience_required = "Unknown"
                    skills = "In Development" # Still in development
                    resume = "Pending"
                    reposted = False
                    questions_list = None
                    screenshot_name = "Not Available"

                    try:
                        rejected_jobs, blacklisted_companies, jobs_top_card = check_blacklist(rejected_jobs,job_id,company,blacklisted_companies)
                    except ValueError as e:
                        print_lg(e, 'Skipping this job!\n')
                        failed_job(job_id, job_link, resume, date_listed, "Found Blacklisted words in About Company", e, "Skipped", screenshot_name)
                        skip_count += 1
                        continue
                    except Exception as e:
                        print_lg("Failed to scroll to About Company!")
                        # print_lg(e)

                    # Hiring Manager info
                    try:
                        hr_info_card = WebDriverWait(driver,2).until(EC.presence_of_element_located((By.CLASS_NAME, "hirer-card__hirer-information")))
                        hr_link = hr_info_card.find_element(By.TAG_NAME, "a").get_attribute("href")
                        hr_name = hr_info_card.find_element(By.TAG_NAME, "span").text        
                    except Exception as e:
                        print_lg(f'HR info was not given for "{title}" with Job ID: {job_id}!')
                        # print_lg(e)

                    # Calculation of date posted
                    try:
                        # try: time_posted_text = find_by_class(driver, "jobs-unified-top-card__posted-date", 2).text
                        # except: 
                        time_posted_text = jobs_top_card.find_element(By.XPATH, './/span[contains(normalize-space(), " ago")]').text
                        print("Time Posted: " + time_posted_text)
                        if time_posted_text.__contains__("Reposted"):
                            reposted = True
                            time_posted_text = time_posted_text.replace("Reposted", "")
                        date_listed = calculate_date_posted(time_posted_text)
                    except Exception as e:
                        print_lg("Failed to calculate the date posted!",e)

                    # Get job description
                    try:
                        found_masters = 0
                        description = find_by_class(driver, "jobs-box__html-content").text
                        descriptionLow = description.lower()
                        skip = False
                        for word in bad_words:
                            if word.lower() in descriptionLow:
                                message = f'\n{description}\n\nContains bad word "{word}". Skipping this job!\n'
                                reason = "Found a Bad Word in About Job"
                                skip = True
                                break
                        if not skip and security_clearance == False and ('polygraph' in descriptionLow or 'clearance' in descriptionLow or 'secret' in descriptionLow):
                            message = f'\n{description}\n\nFound "Clearance" or "Polygraph". Skipping this job!\n'
                            reason = "Asking for Security clearance"
                            skip = True
                        if not skip:
                            if did_masters and 'master' in descriptionLow:
                                print_lg(f'Found the word "master" in \n{description}')
                                found_masters = 2
                            experience_required = extract_years_of_experience(description)
                            if current_experience > -1 and experience_required > current_experience + found_masters:
                                message = f'\n{description}\n\nExperience required {experience_required} > Current Experience {current_experience + found_masters}. Skipping this job!\n'
                                reason = "Required experience is high"
                                skip = True
                        if skip:
                            print_lg(message)
                            failed_job(job_id, job_link, resume, date_listed, reason, message, "Skipped", screenshot_name)
                            rejected_jobs.add(job_id)
                            skip_count += 1
                            continue
                    except Exception as e:
                        if description == "Unknown":    print_lg("Unable to extract job description!")
                        else:
                            experience_required = "Error in extraction"
                            print_lg("Unable to extract years of experience required!")
                        # print_lg(e)

                    uploaded = False
                    # Case 1: Easy Apply Button
                    if wait_span_click(driver, "Easy Apply", 2):
                        try: 
                            try:
                                errored = ""
                                modal = find_by_class(driver, "jobs-easy-apply-modal")
                                wait_span_click(modal, "Next", 1)
                                # if description != "Unknown":
                                #     resume = create_custom_resume(description)
                                resume = "Previous resume"
                                next_button = True
                                questions_list = set()
                                next_counter = 0
                                while next_button:
                                    next_counter += 1
                                    if next_counter >= 15: 
                                        if pause_at_failed_question:
                                            screenshot(driver, job_id, "Needed manual intervention for failed question")
                                            pyautogui.alert("Couldn't answer one or more questions.\nPlease click \"Continue\" once done.\nDO NOT CLICK Back, Next or Review button in LinkedIn.\n\n\n\n\nYou can turn off \"Pause at failed question\" setting in config.py", "Help Needed", "Continue")
                                            next_counter = 1
                                            continue
                                        # if questions_list: print_lg("Stuck for one or some of the following questions...", questions_list)
                                        # screenshot_name = screenshot(driver, job_id, "Failed at questions")
                                        # errored = "stuck"
                                        # raise Exception("Seems like stuck in a continuous loop of next, probably because of new questions.")
                                    questions_list = answer_questions(questions_list, work_location)
                                    if useNewResume and not uploaded: uploaded, resume = upload_resume(modal, default_resume_path)
                                    try: next_button = modal.find_element(By.XPATH, './/span[normalize-space(.)="Review"]') 
                                    except NoSuchElementException:  next_button = modal.find_element(By.XPATH, './/button[contains(span, "Next")]')
                                    try: next_button.click()
                                    except ElementClickInterceptedException: break    # Happens when it tries to click Next button in About Company photos section
                                    buffer(click_gap)

                            except NoSuchElementException: errored = "nose"
                            finally:
                                if questions_list and errored != "stuck": 
                                    print_lg("Answered the following questions...", questions_list)
                                    print("\n\n" + "\n".join(str(question) for question in questions_list) + "\n\n")
                                wait_span_click(driver, "Review", 1, scrollTop=True)
                                cur_pause_before_submit = pause_before_submit
                                if errored != "stuck" and cur_pause_before_submit:
                                    decision = pyautogui.confirm('1. Please verify your information.\n2. If you edited something, please return to this final screen.\n3. DO NOT CLICK "Submit Application".\n\n\n\n\nYou can turn off "Pause before submit" setting in config.py\nTo TEMPORARILY disable pausing, click "Disable Pause"', "Confirm your information",["Disable Pause", "Discard Application", "Submit Application"])
                                    if decision == "Discard Application": raise Exception("Job application discarded by user!")
                                    pause_before_submit = False if "Disable Pause" == decision else True
                                    try_xp(modal, ".//span[normalize-space(.)='Review']")
                                if wait_span_click(driver, "Submit application", 2, scrollTop=True): 
                                    date_applied = datetime.now()
                                    if not wait_span_click(driver, "Done", 2): actions.send_keys(Keys.ESCAPE).perform()
                                elif errored != "stuck" and cur_pause_before_submit and "Yes" in pyautogui.confirm("You submitted the application, didn't you 😒?", "Failed to find Submit Application!", ["Yes", "No"]):
                                    date_applied = datetime.now()
                                    wait_span_click(driver, "Done", 2)
                                else:
                                    print_lg("Since, Submit Application failed, discarding the job application...")
                                    # if screenshot_name == "Not Available":  screenshot_name = screenshot(driver, job_id, "Failed to click Submit application")
                                    # else:   screenshot_name = [screenshot_name, screenshot(driver, job_id, "Failed to click Submit application")]
                                    if errored == "nose": raise Exception("Failed to click Submit application 😑")


                        except Exception as e:
                            print_lg("Failed to Easy apply!")
                            # print_lg(e)
                            critical_error_log("Somewhere in Easy Apply process",e)
                            failed_job(job_id, job_link, resume, date_listed, "Problem in Easy Applying", e, application_link, screenshot_name)
                            failed_count += 1
                            discard_job()
                            continue
                    else:
                        # Case 2: Apply externally
                        skip, application_link, tabs_count = external_apply(pagination_element, job_id, job_link, resume, date_listed, application_link, screenshot_name)
                        if dailyEasyApplyLimitReached:
                            print_lg("\n###############  Daily application limit for Easy Apply is reached!  ###############\n")
                            return
                        if skip: continue

                    submitted_jobs(job_id, title, company, work_location, work_style, description, experience_required, skills, hr_name, hr_link, resume, reposted, date_listed, date_applied, job_link, application_link, questions_list, connect_request)
                    if uploaded:   useNewResume = False

                    print_lg(f'Successfully saved "{title} | {company}" job. Job ID: {job_id} info')
                    current_count += 1
                    if application_link == "Easy Applied": easy_applied_count += 1
                    else:   external_jobs_count += 1
                    applied_jobs.add(job_id)

                # Switching to next page
                if pagination_element == None:
                    print_lg("Couldn't find pagination element, probably at the end page of results!")
                    break
                try:
                    pagination_element.find_element(By.XPATH, f"//button[@aria-label='Page {current_page+1}']").click()
                    print_lg(f"\n>-> Now on Page {current_page+1} \n")
                except NoSuchElementException:
                    print_lg(f"\n>-> Didn't find Page {current_page+1}. Probably at the end page of results!\n")
                    break

        except Exception as e:
            print_lg("Failed to find Job listings!")
            critical_error_log("In Applier", e)
            # print_lg(e)
        
def run(total_runs: int) -> int:
    if dailyEasyApplyLimitReached:
        return total_runs
    print_lg("\n" + "#" * 120 + "\n")
    print_lg(f"Date and Time: {datetime.now()}")
    print_lg(f"Cycle number: {total_runs}")
    print_lg(f"Looking for jobs posted within '{date_posted}' and sorting by '{sort_by}'")
    apply_to_jobs(search_terms)
    return total_runs + 1

chatGPT_tab = False
linkedIn_tab = False

def main() -> None:
    try:
        global linkedIn_tab, tabs_count, useNewResume
        total_runs = 1
        validate_config()

        if not os.path.exists(default_resume_path):
            pyautogui.alert(
                text=f'Your default resume "{default_resume_path}" is missing! Please update its folder path in config.py or add the resume with the exact name and path. The bot will use your previous upload from LinkedIn.',
                title="Missing Resume", button="OK"
            )
            useNewResume = False

        # LinkedIn login
        tabs_count = len(driver.window_handles)
        driver.get("https://www.linkedin.com/login")
        if not is_logged_in_LN(): login_LN()
        linkedIn_tab = driver.current_window_handle

        # Job applying cycle
        driver.switch_to.window(linkedIn_tab)
        total_runs = run(total_runs)

        while run_non_stop:
            # Cycle through date posted options
            if cycle_date_posted:
                date_options = ["Any time", "Past month", "Past week", "Past 24 hours"]
                date_posted = date_options[0 if (idx := date_options.index(date_posted)) + 1 >= len(date_options) else idx + 1]
            
            # Alternate between sorting options
            if alternate_sortby:
                global sort_by
                sort_by = "Most recent" if sort_by == "Most relevant" else "Most relevant"
                total_runs = run(total_runs)

            total_runs = run(total_runs)
            if dailyEasyApplyLimitReached: break

    except NoSuchWindowException:
        pass
    except Exception as e:
        critical_error_log("In Applier Main", e)
        pyautogui.alert(e, "Error Occurred. Closing Browser!")
    
    finally:
        summary = (
            f"\n\nTotal runs: {total_runs}\n"
            f"Jobs Easy Applied: {easy_applied_count}\n"
            f"External job links collected: {external_jobs_count}\n"
            f"Total applied or collected: {easy_applied_count + external_jobs_count}\n"
            f"Failed jobs: {failed_count}\n"
            f"Irrelevant jobs skipped: {skip_count}"
        )
        print_lg(summary)

        if randomly_answered_questions:
            print_lg(f"\n\nQuestions randomly answered:\n  {';\n'.join(str(q) for q in randomly_answered_questions)}\n\n")

        print_lg("Closing the browser...")
        if tabs_count >= 10:
            msg = "NOTE: If you have more than 10 tabs opened, please close or bookmark them. Otherwise, the application might not work next time!"
            pyautogui.alert(msg, "Info")
            print_lg(f"\n{msg}")
        try:
            driver.quit()
        except Exception as e:
            critical_error_log("When quitting...", e)

if __name__ == "__main__":
    main()
