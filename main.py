from funcs_imports import *

# Set the logging level to suppress less critical messages
logging.getLogger('urllib3').setLevel(logging.WARNING)

current_date = get_current_datetime('date')
report_output = set_output_folder('report')
report_file = os.path.join(report_output, f'Report {current_date}.txt')
# Create empty file
with open(report_file, 'w') as file:
    pass

driver_choice = input("Start driver PCO licence check? (Y/N): ")
print('\n')

if driver_choice == 'y' or driver_choice == 'Y':
    # Create chrome options with headless mode
    driver = setup_chrome_driver()
    # Set driver.csv input file
    driver_file_path = set_input_file('drivers')
    # Set the output for the search results
    driver_output = set_output_folder('drivers')

    # Make sure CSV file is in correct format
    clean_csv_file(driver_file_path)

    # Load the driver CSV file
    driver_file = pandas.read_csv(driver_file_path)
    # List to store licence numbers that could not be found
    drivers_not_found = []
    # List to store licence numbers that have been found
    drivers_completed = []

    for index, licence_number in enumerate(driver_file['Private Hire Driver License Number']):
        # noinspection PyRedeclaration
        original_licence_number = str(licence_number) # Convert to string for manipulation
        original_licence_number = original_licence_number[:6]
        # noinspection PyRedeclaration
        surname = driver_file.iloc[index]['Surname']
        surname_split = surname.split()  # Split by spaces
        surname = surname_split[-1]
        stop_event = threading.Event()
        search_thread = threading.Thread(target=searching_animation, args=('driver licence number', licence_number, stop_event,))
        search_thread.start()

        search_attempts = 0

        while search_attempts < 3:  # Try three different variations of the licence number
            # Navigate to the TFL Licence checker website
            driver.get(DRIVER_PAGE)
            # Find the search box and enter the licence number
            search_box = driver.find_element(by='name', value=DRIVER_SEARCH_BOX)
            search_box.send_keys(original_licence_number)
            search_box.send_keys(Keys.RETURN)
            # Wait for the page to load
            time.sleep(5)

            # Check if the licence number was found
            if "Please check the following and try again:" in driver.page_source:
                # Reduce the length of the licence number and try again
                original_licence_number = original_licence_number[:-1] # Cut off the last digit
                search_attempts += 1
            else:
                # If licence number was found, capture screenshot with driver's name and exit the loop
                driver_name_element = driver.find_element(by='xpath', value=DRIVER_NAME_ELEMENT)
                driver_name = driver_name_element.text.strip()
                driver_name = remove_prefix(driver_name)

                licence_surname = driver_name.split()
                licence_surname = licence_surname[-1]

                if surname.lower() == licence_surname.lower():   # Only save the screenshot if the name on the website matches the name on the csv file
                    # Capture a screenshot of the page and save it as a PNG
                    screenshot_path = os.path.join(driver_output, f'{driver_name}.png')
                    driver.save_screenshot(screenshot_path)
                    stamp_datetime(screenshot_path)

                    # Add to the list of successfully searches
                    drivers_completed.append(driver_name)

                    # Stop the searching animation
                    stop_event.set()
                    print(COMPLETE)

                    break  # Exit the loop if the screenshot is successfully captured
                else:
                    original_licence_number = original_licence_number[:-1]  # Cut off the last digit
                    search_attempts += 1

            # If all attempts have failed, add the original licence number to the not found list
            if search_attempts == 3:
                drivers_not_found.append(licence_number)
                stop_event.set()
                print(COMPLETE)

    # Close the web driver
    driver.quit()

    # Generate report
    generate_report('driver licence', report_file, drivers_completed, drivers_not_found)
    print("\nReport generated")
    # Convert all PNG screenshots to PDF
    convert_pdf(driver_output)

vehicle_choice = input("\n\nContinue with vehicle licence checks? (Y/N): ")
print('\n')

if vehicle_choice == 'y' or vehicle_choice == 'Y':
    # Create chrome options with headless mode
    driver = setup_chrome_driver()
    # Get vehicles.csv file
    vehicle_file_path = set_input_file('vehicles')
    # Set output folder for search results
    vehicle_output = set_output_folder('vehicles')

    # Clean the csv file
    clean_csv_file(vehicle_file_path)
    # Load the csv file
    vehicle_file = pandas.read_csv(vehicle_file_path)

    # List to store the reg plate numbers that couldn't be found
    vehicles_not_found = []
    # List to store the reg plate numbers that couldn't be found
    vehicles_completed = []

    # Iterate over the reg numbers in the CSV file
    for index, licence_number in enumerate(vehicle_file['Vehicle License Number']):

        original_licence_number = str(licence_number)
        original_licence_number = original_licence_number[:6]
        reg_number = vehicle_file.iloc[index]['VRM']
        reg_number = reg_number.replace(" ", "")

        new_search_attempts = 0

        stop_event = threading.Event()
        search_thread = threading.Thread(target=searching_animation, args=('vehicle licence number',
                                                                           licence_number, stop_event,))
        search_thread.start()

        while new_search_attempts < 3:
            # Navigate to the TFL Licence checker
            driver.get(VEHICLE_PAGE)

            # Find the search box and enter the vehicle licence number
            search_box = driver.find_element(by='name', value=VEHICLE_SEARCH_BOX)
            search_box.send_keys(original_licence_number)
            search_box.send_keys(Keys.RETURN)
            # Wait for the page to load
            time.sleep(5)

            # check if the licence number was found
            if "Please check the following and try again:" in driver.page_source:
                original_licence_number = original_licence_number[:-1]
                new_search_attempts+=1
            else:
                # if licence number was found, capture screenshot with reg number and exit the loop
                reg_number_element = driver.find_element(by='xpath', value=REG_NUMBER_ELEMENT)
                web_reg_number = reg_number_element.text.strip()

                if reg_number in web_reg_number:
                    # Capture screenshot and save as PNG
                    screenshot_path = os.path.join(vehicle_output, f'{reg_number}.png')
                    driver.save_screenshot(screenshot_path)
                    # Stamp the date and time of the check on the image
                    stamp_datetime(screenshot_path)

                    stop_event.set()
                    print(COMPLETE)

                    # Add completed search to the completed list
                    vehicles_completed.append(reg_number)

                    break
                else:
                    original_licence_number = original_licence_number[:-1]
                    new_search_attempts += 1

            if new_search_attempts == 3:
                vehicles_not_found.append(reg_number)
                stop_event.set()
                print(COMPLETE)

    # CLose the web driver
    driver.quit()

    # Generate report
    generate_report('reg plate', report_file, vehicles_completed, vehicles_not_found)
    print("\nReport updated")
    #Convert to PDF
    convert_pdf(vehicle_output)