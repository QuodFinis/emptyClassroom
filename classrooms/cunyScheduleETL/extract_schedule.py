import csv
from datetime import datetime

from playwright.sync_api import sync_playwright
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def setupSearch(page):
    # set search criteria
    logging.info("Setting up search")
    page.get_by_role("listitem").filter(has_text="Baruch College").locator("span").click()
    page.get_by_label("Term").select_option(index=1)
    page.get_by_role("button", name="Next").click()
    page.locator(".slider").first.click()
    # page.get_by_role("listitem").filter(has_text="HyFlex").locator("span").click()
    page.get_by_role("listitem").filter(has_text="Hybrid Synchronous").locator("span").click()
    page.get_by_role("listitem").filter(has_text="In Person").locator("span").click()
    page.get_by_role("listitem").filter(has_text="Hybrid Asynchronous").locator("span").click()
    page.get_by_label("Subject").select_option("ACCT")
    page.get_by_role("button", name="Search").click()
    page.get_by_role("button", name="Modify Search").click()
    page.get_by_role("listitem").filter(has_text="Baruch College").locator("span").click()
    page.get_by_label("Term").select_option("")
    logging.info("Search setup complete")

def extract(college_names=None, subjects=None, DEBUG=False):
    with sync_playwright() as playwright:
        logging.info("Launching browser...")
        # Configure browser with headers and visibility
        browser = playwright.chromium.launch(
            headless=(not DEBUG),
            args=['--disable-blink-features=AutomationControlled']
        )

        # Set user agent and headers
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.cuny.edu/',
            },
            viewport=None
        )

        page = context.new_page()
        page.set_default_timeout(60000)  # 60 seconds timeout

        logging.info("Navigating to CUNY Global Search Tool...")
        page.goto("https://globalsearch.cuny.edu/CFGlobalSearchTool/search.jsp", wait_until="networkidle")

        setupSearch(page)

        # if list of college names are passed then get the checkbox locators for those colleges
        checkboxes = []
        if college_names:
            for college_name in college_names:
                try:
                    checkboxes.append(page.get_by_role("listitem").filter(has_text=college_name))
                except:
                    logging.error(f"College not found: {college_name}")
                    continue
        else:
            checkbox_ids = [locator.get_attribute('id') for locator in page.locator('ul.checkboxes input[type="checkbox"]').all()]
            checkboxes = [page.locator(f'label[for="{checkbox_id}"]') for checkbox_id in checkbox_ids]

        # write to csv file
        with open('cuny_schedule.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            #write header college_name,term,subject,course_code,course_name,building,room,start_date,end_date,days,start_time,end_time
            writer.writerow([
                'college_name', 'term', 'subject', 'course_code', 'course_name', 'building', 'room',
                'start_date', 'end_date', 'days', 'start_time', 'end_time'
            ])

        # loop through all the colleges
        for label in checkboxes:
            college_name = label.inner_text()
            label.locator("span").click()
            logging.info(f"{college_name}")

            # Get current term
            term_dropdown = page.get_by_label('Term')
            term_options = term_dropdown.locator('option').all()
            term_months = {1: 3, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 2, 9: 1, 10: 1, 11: 1, 12: 1}
            term_option = term_options[term_months[datetime.now().month]]
            term_value =  term_option.get_attribute('value')
            term_dropdown.select_option(term_value)  # Select current term
            term =  term_option.inner_text()
            logging.info(f"{college_name} {term}")

            #page.get_by_role('button', name='Next').click()  # Go to next page
            page.locator('input[value="Next"]').click()  # Click on the next button

            # Get subjects
            subject_dropdown = page.get_by_label('Subject')
            subject_options = subject_dropdown.locator('option').all()
            if len(subject_options) == 1: # Skip if no subjects found
                logging.info("No subjects found for this term.")
                # back_button = page.get_by_role("button", name="Back")
                back_button = page.locator('input[value="Back"]')
                back_button.click()
                continue

            # TODO: Add functionality to filter for specific subjects incase wanting to update

            # loop through the subjects
            schedule_entries = []
            total_classes_found = 0
            total_classes_added = 0
            for subject_option in subject_options[1:]:
                subject = subject_option.inner_text()
                subject_dropdown.select_option(value=subject_option.get_attribute('value'))
                logging.info(f"{college_name} {term} {subject}")

                # search_button = page.get_by_role("button", name="Search")
                search_button = page.locator('input[value="Search"]')
                search_button.click()

                no_results = page.evaluate('''() => document.body.textContent.includes("The search returns no results")''')
                if no_results:
                    logging.info("No results found for this subject.")
                    continue

                # Expand all sections
                page.evaluate('''() => {
                    document.querySelectorAll('[aria-label="Class Section"], [aria-label="Class Section Sub"]')
                        .forEach(el => el.click());
                }''')
                #logging.info('All sections expanded.')

                # Extract table rows for the course
                tables = page.locator("form[name=\"form_search\"] table").locator("tbody tr").all()
                #logging.info(f"Found {len(tables)} courses.")
                classes_found = len(tables)
                classes_added = 0
                for table in tables:
                    cells = table.locator('td')
                    courseCode = cells.nth(0).inner_text()
                    daysAndTimes = cells.nth(2).inner_html().split('<br>')
                    rooms = cells.nth(3).inner_html().split('<br>')
                    dates = cells.nth(6).inner_html().split('<br>')
                    courseName = cells.nth(8).inner_text()
                    if len(rooms) < len(daysAndTimes): rooms = [rooms[0]] * len(daysAndTimes)

                    for j in range(len(daysAndTimes)):
                        # filter out TBA and - in dayTimes and rooms
                        if (daysAndTimes[j].strip() in ('TBA', '-', '-')) or (rooms[j] in ('TBA', '-', 'Online-Asynchronous', 'Online-Synchronous', 'Off-Campus')):
                            continue

                        # split days and times
                        parts = daysAndTimes[j].split(' ')
                        if len(parts) != 4 or parts[1] == '' or parts[3] == '':
                            logging.error(f"Error parsing days and times: {daysAndTimes[j]}")
                            logging.error(f"{college_name} {term} {subject} {courseCode} {courseName}")
                            continue
                        days, start_time, _, end_time = parts
                        start_date, _, end_date = dates[j].split(' ')

                        # split room which contains building and specific room
                        room = rooms[j].split(' ')[-1]
                        building = ' '.join(rooms[j].split(' ')[:-1])

                        entry = {
                            'college_name': college_name,
                            'term': term,
                            'subject': subject,
                            'course_code': courseCode,
                            'course_name': courseName,
                            'building': building,
                            'room': room,
                            'days': days,
                            'start_time': start_time,
                            'end_time': end_time,
                            'start_date': start_date,
                            'end_date': end_date,
                        }
                        schedule_entries.append(entry)
                        classes_added += 1

                total_classes_found += classes_found
                total_classes_added += classes_added
                logging.info(f"Finished {college_name} {subject} - {classes_added} of {classes_found}.")

                # Go back to course selection page to select next subject
                # page.get_by_role("button", name="Modify Search").click()
                page.locator('input[value="Modify Search"]').click()
                # page.get_by_role('button', name='Next').click()
                page.locator('input[value="Next"]').click()

            # write to csv file
            with open('cuny_schedule.csv', 'a', newline='') as f:
                writer = csv.writer(f)
                for entry in schedule_entries:
                    writer.writerow([
                        entry['college_name'], entry['term'], entry['subject'], entry['course_code'],
                        entry['course_name'], entry['building'], entry['room'],
                        entry['start_date'], entry['end_date'], entry['days'],
                        entry['start_time'], entry['end_time']
                    ])

            # go back to college select page, deselect college and then click on the college name
            logging.info(f"Finished {college_name} - {total_classes_added} of {total_classes_found}.")
            # page.get_by_role('button', name='Back').click()
            page.locator('input[value="Back"]').click()
            label.click()

        logging.info("Finished processing all colleges.")
        browser.close()




if __name__ == "__main__":
    # for testing
    college_names = ['City College']
    extract(college_names=college_names, DEBUG=True)

    # for dev
    # playwright codegen https://globalsearch.cuny.edu/CFGlobalSearchTool/search.jsp
    # for testing
    # $Env:PWDEBUG=1; python .\classrooms\cunyScheduleETL\extract.py