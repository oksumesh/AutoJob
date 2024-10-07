# These search terms are used in LinkedIn's search bar.
# Enter your search terms inside '[ ]', each enclosed in quotes. 
# Example: ["Software Engineer", "Software Developer", "Selenium Developer"]
search_terms = []

# The location to search in. This value is filled in the "City, state, or zip code" search box.
# Leave empty as "", and the tool will skip this field.
search_location = ""  # Examples: "", "United States", "India", "Chicago, Illinois, United States", "90001, Los Angeles, California, United States", "Bengaluru, Karnataka, India"

# After how many applications should the tool switch to the next search term?
switch_number = 50  # Enter a number greater than 0 (no quotes).

# Do you want to randomize the order of search terms?
randomize_search_order = False  # True or False


# >>>>>>>>>>> Job Search Filters <<<<<<<<<<<
sort_by = ""  # "Most recent", "Most relevant", or leave empty ("") to skip sorting

date_posted = ""  # "Any time", "Past month", "Past week", "Past 24 hours" or leave empty ("") to skip

salary = ""  # Salary filters, examples: "$40,000+", "$60,000+", "$100,000+" or leave empty ("")

easy_apply_only = True  # True or False, filters jobs with the 'Easy Apply' option

experience_level = []  # (multiple select) "Internship", "Entry level", "Associate", "Mid-Senior level", "Director", "Executive"
job_type = []  # (multiple select) "Full-time", "Part-time", "Contract", "Temporary", "Volunteer", "Internship", "Other"
on_site = ["Remote"]  # (multiple select) "On-site", "Remote", "Hybrid"

companies = []  # (dynamic multiple select) Enter the exact company name(s), case-sensitive.
                # Examples: ["Google", "Apple", "Netflix", "Microsoft"]

location = []  # (dynamic multiple select) Specific job location preferences
industry = []  # (dynamic multiple select) Specific industries to filter
job_function = []  # (dynamic multiple select) Job functions to filter
job_titles = []  # (dynamic multiple select) Specific job titles to filter
benefits = []  # (dynamic multiple select) Job benefits to filter
commitments = []  # (dynamic multiple select) Job commitments to filter

under_10_applicants = False  # True or False, filters jobs with fewer than 10 applicants
in_your_network = False  # True or False, filters jobs posted by people in your network
fair_chance_employer = False  # True or False, filters jobs from "Fair Chance" employers


# >>>>>>>>>>> SKIP IRRELEVANT JOBS <<<<<<<<<<<

# Skip applying to companies with these words in their 'About Company' section.
about_company_bad_words = []  # (dynamic multiple select) Examples: ["Staffing", "Recruiting", "Agency"]

# Ignore `about_company_bad_words` for companies that have these words in their 'About Company' section (exceptions).
about_company_good_words = []  # (dynamic multiple select) Examples: ["Robert Half", "Dice"]

# Skip applying to jobs with these words in their job description.
bad_words = ["US Citizen", "USA Citizen", "No C2C", "No Corp2Corp", "PHP", "Ruby", "CNC"]  # (dynamic multiple select), case-insensitive

# Do you have an active security clearance?
security_clearance = False  # True for Yes, False for No

# Do you have a Master's degree?
did_masters = True  # True or False, filters jobs requiring a Master's degree

# Skip jobs requiring experience above your current_experience. 
# Set to -1 to apply to all jobs regardless of experience required.
current_experience = 5  # Integer greater than -2 (e.g., -1, 0, 1, 5...)