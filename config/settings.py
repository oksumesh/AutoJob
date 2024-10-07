# >>>>>>>>>>> LinkedIn Settings <<<<<<<<<<<

# Keep external application tabs open? (RECOMMENDED: Leave this as True)
# If set to False, be sure to CLOSE ALL TABS BEFORE CLOSING THE BROWSER to avoid issues.
close_tabs = True  # True or False

## Upcoming features (In Development)
# # Automatically send connection requests to HRs
# connect_hr = True  # True or False

# # Customize the message sent with connection requests (Max. 200 characters).
# # Leave empty ("") to send the request without a personalized message.
# connect_request_message = ""  # (Recommended to leave this empty if you don't have LinkedIn Premium)

# Should the program run continuously until manually stopped? (Beta)
run_non_stop = True  # True or False (Will be treated as False if run_in_background is True)
alternate_sortby = True  # True or False, to alternate between different sort options
cycle_date_posted = True  # True or False, to cycle through date posted filters
stop_date_cycle_at_24hr = True  # True or False, stop cycling when it reaches "Past 24 hours" filter


# >>>>>>>>>>> RESUME GENERATOR (Experimental & In Development) <<<<<<<<<<<

# Path to the folder where generated resumes will be stored.
generated_resume_path = "resume/"  # (In Development)


# >>>>>>>>>>> Global Settings <<<<<<<<<<<

# File paths for saving job application history.
# The last part after the "/" will be used as the file name.
file_name = "data/applied.csv"
failed_file_name = "data/failed.csv"
logs_folder_path = "logs/"

# Maximum time to wait between clicks (in seconds).
click_gap = 0  # Only non-negative integers, e.g., 0, 1, 2, 3,...

# If you want to see the Chrome browser running, set run_in_background to False.
# (Setting this to False may reduce performance.)
run_in_background = False  # True or False (If True, it will disable pause_at_failed_question, pause_before_submit, and run_in_background)

# Disable browser extensions for better performance.
disable_extensions = True  # True or False

# Run Chrome in safe mode (guest profile) if it's taking too long to open or if there are multiple profiles in the browser.
safe_mode = True  # True or False

# Enable smooth scrolling for better user experience (may reduce performance).
smooth_scroll = False  # True or False

# Keep your screen active to prevent the PC from sleeping. 
# (Temporarily deactivates when dialogs are present, e.g., "Pause before submit".)
keep_screen_awake = True  # True or False (Alternative: adjust PC sleep settings)

# Run in undetected mode to bypass anti-bot protections (Preview feature, unstable).
# (Recommended to leave this as False.)
stealth_mode = True  # True or False