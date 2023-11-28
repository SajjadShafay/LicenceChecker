import os
import pandas
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import sys
import re
import threading
from PIL import Image, ImageDraw, ImageFont
import img2pdf
import datetime
import tkinter
from tkinter import filedialog
import logging

sys.stderr = open(os.devnull, 'w')

# Set the logging level to suppress less critical messages
logging.getLogger('urllib3').setLevel(logging.WARNING)

COMPLETE = "................Complete"

FONT = 'SwanseaBold.ttf'
FONT_SIZE = 16
FONT_COLOR = 'white'

DRIVER_PAGE = ('https://tph.tfl.gov.uk/TfL/SearchDriverLicence.page?org.apache.shale.dialog.DIALOG_NAME'
               '=TPHDriverLicence&Param=lg2.TPHDriverLicence&menuId=6')
VEHICLE_PAGE = ('https://tph.tfl.gov.uk/TfL/SearchVehicleLicence.page?org.apache.shale.dialog.DIALOG_NAME'
                '=TPHVehicleLicence&Param=lg2.TPHVehicleLicence&menuId=7')

DRIVER_SEARCH_BOX = 'searchdriverlicenceform:DriverLicenceNo'
DRIVER_NAME_ELEMENT = '//*[@id="_id177:driverResults:tbody_element"]/tr/td[2]'

VEHICLE_SEARCH_BOX = 'searchvehiclelicenceform:VehicleVRM'


def remove_prefix(text):
    # Define a regular expression pattern to find prefixes at the beginning of the string
    pattern = r'\b(?:Mrs|Mr|Miss|Ms)\s*'

    # Use a re.sub() to remove occurrences of prefixes from the string
    cleaned_text = re.sub(pattern, '', text)

    return cleaned_text


def searching_animation(search_term, search_item, stop_event):
    dot_count = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\rSearching for {search_term}: {search_item}{'.' * dot_count}{' ' * (3 - dot_count)}")
        sys.stdout.flush()
        time.sleep(0.5)
        dot_count = (dot_count + 1) % 4 # Cycle through 3 dots
    return


def get_current_datetime(text):  # Text is either 'full' for Date + Time and 'date' for only the date
    now = datetime.datetime.now()
    if text == 'full':
        return now.strftime("%d-%m-%Y %H:%M")
    else:
        return now.strftime("%d-%m-%Y")


def set_output_folder(file_to_save):
    root = tkinter.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    output = filedialog.askdirectory(parent=root, initialdir=r"\\AJMTDrive\AJMT", title=f"Please select an output fold"
                                                                                        f"er for the {file_to_save}")
    root.deiconify()
    root.withdraw()
    return output


def setup_chrome_driver():
    # Create Chrome options with headless mode
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--log-level=3')
    # Set up the web driver
    driver = webdriver.Chrome(options=chrome_options)

    return driver


def set_input_file(file):
    root = tkinter.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    file_path = filedialog.askopenfilename(parent=root, initialdir=r"\\AJMTDrive\AJMT", title=f"Please select {file}.c"
                                                                                              "sv file")
    root.deiconify()
    root.withdraw()
    return file_path


def clean_csv_file(file_path):
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


def stamp_datetime(screenshot_path):
    # Stamp the date and time of the check on the image
    img = Image.open(screenshot_path)
    now = get_current_datetime('full')
    # Set the font and size for the timestamp
    font = ImageFont.load_default()
    # Add the timestamp to the screenshot
    draw = ImageDraw.Draw(img)
    draw.text((40, 120), now, font=font, fill=FONT_COLOR)
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


def generate_report(item, report_file, items_completed, items_not_found):
    now = get_current_datetime('full')
    with open(report_file, mode='a+') as report:
        report.write(f"Driver check completed on {str(now)}")
        report.write(f"\n\nThe following {item} numbers were successfully found:")
        for completed in items_completed:
            report.write(f"\n{str(completed)}")
        report.write('\n')
        report.write(f"\nThe following {item} numbers could not be found:")
        for not_found in items_not_found:
            report.write(f"\n{str(not_found)}")
        report.write('\n\n')


def convert_pdf(output_file):
    for filename in os.listdir(output_file):
        if filename.endswith('.png'):
            # File path for the current PNG image
            png_file_path = os.path.join(output_file, filename)
            # File path for the PDF (replace the .png extension with .pdf
            pdf_file_path = os.path.splitext(png_file_path)[0] + '.pdf'
            # Convert PNG to PDF
            with open(pdf_file_path, "wb") as pdf_file:
                pdf_file.write(img2pdf.convert(png_file_path))
            # Remove PNG file
            os.remove(png_file_path)
