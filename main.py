import os
import pandas
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import re
from PIL import Image, ImageDraw, ImageFont
import img2pdf
import datetime

# TODO: Dialog boxes to open files rather than explicitly naming them in code
# TODO: Optimize Code - reduce amount of repeated code


def remove_prefix(text):
    # Define a regular expression pattern to find prefixes at the beginning of the string
    pattern = r'\b(?:Mrs|Mr|Miss|Ms)\s*'

    # Use re.sub() to remove occurrences of "Mr." or "Miss" from the string
    cleaned_text = re.sub(pattern, '', text)

    return cleaned_text


DRIVER_PAGE = ('https://tph.tfl.gov.uk/TfL/SearchDriverLicence.page?org.apache.shale.dialog.DIALOG_NAME'
               '=TPHDriverLicence&Param=lg2.TPHDriverLicence&menuId=6')
VEHICLE_PAGE = ('https://tph.tfl.gov.uk/TfL/SearchVehicleLicence.page?org.apache.shale.dialog.DIALOG_NAME'
                '=TPHVehicleLicence&Param=lg2.TPHVehicleLicence&menuId=7')

now = datetime.datetime.now()
current_date = now.strftime("%d-%m-%Y")
report_file = f"Reports\\Report {current_date}.txt"

driver_Choice = input("Start driver pco licence check? (Y/N): ")

if driver_Choice == 'y' or driver_Choice == 'Y':
    # Set up the web driver
    driver = webdriver.Chrome()

    file_path = "Files\\driver.csv"
    # Read the content of the CSV file
    with open(file_path, 'r') as file:
        lines = file.readlines()
    # Check if the header row ends with a comma
    if not lines[0].strip().endswith(','):
        # Append a comma to the header row
        lines[0] = lines[0].rstrip('\n') + ',\n'

        # Write the modified content back to the file
        with open(file_path, 'w') as file:
            file.writelines(lines)

    # load the driver CSV File
    driver_file = pandas.read_csv('Files\\driver.csv')

    # List to store licence numbers that couldn't be found
    drivers_not_found = []

    # List to store licence numbers that have been found
    drivers_completed = []

    # Iterate over the licence numbers in the CSV file:
    for index, licence_number in enumerate(driver_file['Private Hire Driver License Number']):
        original_licence_number = str(licence_number)  # convert to string for manipulation
        original_licence_number = original_licence_number[:6]
        surname = driver_file.iloc[index]['Surname']
        surname_split = surname.split()  # Split by Spaces
        surname = surname_split[-1]

        search_attempts = 0

        while search_attempts < 3:  # Try three different variations of the licence number
            # Navigate to the TFL Licence checker website
            driver.get(DRIVER_PAGE)

            # Find the search box and enter the licence number
            search_box = driver.find_element(by='name', value='searchdriverlicenceform:DriverLicenceNo')
            search_box.send_keys(original_licence_number)
            search_box.send_keys(Keys.RETURN)

            # Wait for the page to load
            time.sleep(5)

            # Check if the licence number was found
            if 'Please check the following and try again:' in driver.page_source:
                # Reduce the length of the licence number and try again
                original_licence_number = original_licence_number[:-1]  # Cut off the last digit
                search_attempts += 1
            else:
                # If licence number found, capture screenshot with the driver's name and exit the loop

                driver_name_element = driver.find_element(by='xpath', value='//*[@id="_id177:driverResults'
                                                                            ':tbody_element"]/tr/td[2]')
                driver_name = driver_name_element.text.strip()

                driver_name = remove_prefix(driver_name)

                licence_surname = driver_name.split()
                licence_surname = licence_surname[-1]

                if surname.lower() == licence_surname.lower():
                    # Capture a screenshot of the page and save it as a PNG
                    screenshot_path = os.path.join('results\\drivers', f'{driver_name}.png')
                    driver.save_screenshot(screenshot_path)

                    # Stamp the date and time of the check on the image
                    img = Image.open(screenshot_path)
                    now = datetime.datetime.now()
                    current_datetime = now.strftime("%d-%m-%Y %H:%M")
                    # Set the font and size for the timestamp
                    font_path = 'SwanseaBold-D0ox.ttf'
                    font_size = 16
                    font = ImageFont.truetype(font_path, font_size)
                    text_color = 'white'
                    # Add the timestamp to the screenshot
                    draw = ImageDraw.Draw(img)
                    draw.text((40, 110), current_datetime, font=font, fill=text_color)
                    # Delete the original screenshot file
                    os.remove(screenshot_path)
                    # Save the screenshot with the timestamp
                    img.save(screenshot_path)

                    # Remove the alpha channel
                    img_alpha = Image.open(screenshot_path)
                    # If the image has an alpha channel, convert it to RGB (removing transparency)
                    if img_alpha.mode in ('RGBA', 'LA') or (img_alpha.mode == 'P' and 'transparency' in img_alpha.info):
                        img_alpha = img_alpha.convert('RGB')
                    # Save the modified image
                    img_alpha.save(screenshot_path)
                    img_alpha.close()

                    # Add to the list of successful searches
                    drivers_completed.append(driver_name)

                    break  # Exit the loop if the screenshot is successfully captured
                else:
                    original_licence_number = original_licence_number[:-1]  # Cut off the last digit
                    search_attempts += 1

        # If all attempts fail, add the original licence number to not_found list
        if search_attempts == 3:
            drivers_not_found.append(licence_number)

    # Close the web driver
    driver.quit()

    # Generate report
    now = datetime.datetime.now()
    current_datetime = now.strftime("%d-%m-%Y %H:%M")
    with open(report_file, mode='w') as report:
        report.write(f"Driver check completed on {str(current_datetime)}")
        report.write("The following driver licence numbers could not be found:")
        for completed in drivers_completed:
            report.write(f"\n{str(completed)}")
        report.write('\n')
        for not_found in drivers_not_found:
            report.write(f"\n{str(not_found)}")

    # Print the drivers that were successfully found
    print('\nDrivers successfully found:', drivers_completed)

    # Print the licence numbers that couldn't be found
    print('\nLicence numbers not found:', drivers_not_found)

    for filename in os.listdir('results\\drivers'):
        if filename.endswith('.png'):
            # File path for the current PNG image
            png_file_path = os.path.join('results\\drivers', filename)

            # File path for the PDF (replace the .png extension with .pdf)
            pdf_file_path = os.path.splitext(png_file_path)[0] + '.pdf'

            # Convert PNG to PDF
            with open(pdf_file_path, "wb") as pdf_file:
                pdf_file.write(img2pdf.convert(png_file_path))

            # Remove PNG file
            os.remove(png_file_path)

vehicle_Choice = input("\n\nContinue with vehicle licence checks? (Y/N): ")

if vehicle_Choice == 'y' or vehicle_Choice == 'Y':
    # Set up the web driver
    driver = webdriver.Chrome()

    file_path = "Files\\vehicles.csv"
    # Read the content of the CSV file
    with open(file_path, 'r') as file:
        lines = file.readlines()
    # Check if the header row ends with a comma
    if not lines[0].strip().endswith(','):
        # Append a comma to the header row
        lines[0] = lines[0].rstrip('\n') + ',\n'

        # Write the modified content back to the file
        with open(file_path, 'w') as file:
            file.writelines(lines)

    # Load the CSV file
    vehicle_file = pandas.read_csv('Files\\vehicles.csv')

    # List to store the licence numbers that couldn't be found
    vehicles_not_found = []

    # List to store the vehicles that have been found
    vehicles_completed = []

    # Iterate over the reg numbers in the CSV file
    for reg_number in vehicle_file['VRM']:
        # Navigate to the TFL Licence checker
        driver.get(VEHICLE_PAGE)

        reg_number = reg_number.replace(" ", "")

        # Find the search box and enter the licence number
        search_box = driver.find_element(by='name', value='searchvehiclelicenceform:VehicleVRM')
        search_box.send_keys(reg_number)
        search_box.send_keys(Keys.RETURN)

        # Wait for the page to load
        time.sleep(5)  # adjust as needed

        # Check if the reg number was found
        if 'Please check the following and try again:' in driver.page_source:
            vehicles_not_found.append(reg_number)
        else:
            # If reg number found, capture screenshot with the reg number and exit the loop

            # Capture a screenshot of the page and save it as a PNG
            screenshot_path = os.path.join('results\\vehicles', f'{reg_number}.png')
            driver.save_screenshot(screenshot_path)

            # Stamp the date and time of the check on the image
            img = Image.open(screenshot_path)
            # Get current Date and time
            now = datetime.datetime.now()
            current_datetime = now.strftime("%d-%m-%Y %H:%M")
            # Set the font and size for the timestamp
            font_path = 'SwanseaBold-D0ox.ttf'
            font_size = 16
            font = ImageFont.truetype(font_path, font_size)
            text_color = 'white'
            # Add the timestamp to the screenshot
            draw = ImageDraw.Draw(img)
            draw.text((40, 110), current_datetime, font=font, fill=text_color)
            # Delete the original screenshot file
            os.remove(screenshot_path)
            # Save the screenshot with the timestamp
            img.save(screenshot_path)

            # Remove the alpha channel
            img_alpha = Image.open(screenshot_path)
            # If the image has an alpha channel, convert it to RGB (removing transparency)
            if img_alpha.mode in ('RGBA', 'LA') or (img_alpha.mode == 'P' and 'transparency' in img_alpha.info):
                img_alpha = img_alpha.convert('RGB')
            # Save the modified image
            img_alpha.save(screenshot_path)
            img_alpha.close()

            # Add completed search to completed list
            vehicles_completed.append(reg_number)

    # Close the web driver
    driver.quit()

    # Generate report
    now = datetime.datetime.now()
    current_datetime = now.strftime("%d-%m-%Y %H:%M")
    with open(report_file, mode='a+') as report:
        report.write('\n')
        report.write(f"\n Vehicle check completed on {str(current_datetime)}")
        for completed in vehicles_completed:
            report.write(f"\n{str(completed)}")
        report.write('\n')
        report.write("The following reg numbers could not be found:")
        for not_found in vehicles_not_found:
            report.write(f"\n{str(not_found)}")

    # Print the vehicles that were successfully found
    print('\nVehicles successfully found:', vehicles_completed)

    # Print the vehicles that couldn't be found
    print('\nVehicles not found:', vehicles_not_found)

    for filename in os.listdir('results\\vehicles'):
        if filename.endswith('.png'):
            # File path for the current PNG image
            png_file_path = os.path.join('results\\vehicles', filename)

            # File path for the PDF (replace the .png extension with .pdf)
            pdf_file_path = os.path.splitext(png_file_path)[0] + '.pdf'

            # Convert PNG to PDF
            with open(pdf_file_path, "wb") as pdf_file:
                pdf_file.write(img2pdf.convert(png_file_path))

            # Remove PNG file
            os.remove(png_file_path)
