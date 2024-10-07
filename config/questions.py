# >>>>>>>>>>> Easy Apply Questions & Inputs <<<<<<<<<<<

# Provide the relative path to your default resume to be uploaded. 
# If the file is not found, the tool will continue using your previously uploaded resume in LinkedIn.
default_resume_path = "resume/yourresume.pdf"  # (In Development)

# Answer to the question about years of experience, distinct from current job experience.
years_of_experience = "10"  # Enter a number in quotes, e.g., "0", "1", "5", "10", etc.

# Do you require visa sponsorship now or in the future?
require_visa = "No"  # "Yes" or "No"

# Provide the link to your portfolio website. Leave empty ("") if you don't want to answer.
website = ""  # Example: "www.yourportfolio.com" or ""

# Provide the link to your LinkedIn profile.
linkedIn = ""  # Example: "https://www.linkedin.com/in/example" or ""

# Status of your citizenship (optional). Some companies may require you to answer this question.
# Available options: 
# "U.S. Citizen/Permanent Resident", "Non-citizen allowed to work for any employer", 
# "Non-citizen allowed to work for current employer", "Non-citizen seeking work authorization", 
# "Canadian Citizen/Permanent Resident", or "Other"
us_citizenship = "Non-citizen allowed to work for any employer"

## COMPANY-SPECIFIC QUESTIONS ##

# Expected salary for American and European companies, or expected CTC for South Asian companies.
desired_salary = 0  # Enter the amount in numbers, e.g., 80000, 100000, 120000 (Do NOT use quotes)
'''
Note: If the question contains "lakhs" (e.g., "expected CTC in lakhs"), 
it will format the number accordingly. Examples:
* 2400000 will be answered as "24.00"
* 850000 will be answered as "8.50"
If asked in months, it will divide by 12. Examples:
* 2400000 will be answered as "200000"
* 850000 will be answered as "70833"
'''

# Current CTC (Compensation) for companies that require numeric input.
current_ctc = 0  # Enter the amount, e.g., 900000, 1200000 (Do NOT use quotes)
'''
Note: If the question contains "lakhs" (e.g., "current CTC in lakhs"), 
it will format the number accordingly. Examples:
* 2400000 will be answered as "24.00"
* 850000 will be answered as "8.50"
If asked in months, it will divide by 12. Examples:
* 2400000 will be answered as "200000"
* 850000 will be answered as "70833"
'''

# (In Development) Currency type for salary inputs. Companies that allow string inputs will use this field.
# currency = "INR"  # Example: "USD", "INR", "EUR", etc.

# How many days is your notice period?
notice_period = 0  # Enter a number without quotes, e.g., 0, 15, 30, 45, etc.
'''
Note: If the question asks for months or weeks (e.g., notice period in months), 
it will convert the number. Examples:
* For notice_period = 66: "66" days, "2" months, or "9" weeks
* For notice_period = 15: "15" days, "0" months, or "2" weeks
'''

# Your LinkedIn headline, e.g., "Software Engineer @ Google, Masters in Computer Science"
headline = ""  # Example: "Headline" or leave empty to skip the question

# Your summary. Use \n for line breaks.
summary = ""
'''
Note: If left empty as "", the tool will not answer the question. However, some companies may require an answer. Use \n for line breaks.
'''

# Your cover letter, use \n for line breaks.
cover_letter = ""
'''
Note: If left empty as "", the tool will not answer the question. Some companies may require a cover letter. Use \n for line breaks.
'''

# The name of your most recent employer.
recent_employer = ""  # Example: "Google", "Databricks", or ""

# Example question: "On a scale of 1-10, how much experience do you have building web or mobile applications?"
confidence_level = ""  # Enter a number between "1" and "10", in quotes.

# >>>>>>>>>>> RELATED SETTINGS <<<<<<<<<<<

## Allow Manual Inputs
# Should the tool pause before each submit during easy apply to let you verify the information?
pause_before_submit = False  # True or False (will default to False if run_in_background is True)

# Should the tool pause if it encounters difficulties answering a question during easy apply?
# If set to False, it will answer randomly.
pause_at_failed_question = False  # True or False (will default to False if run_in_background is True)

# Do you want to overwrite previous answers during easy apply?
overwrite_previous_answers = False  # True or False