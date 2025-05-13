import os
import asyncio
import aiofiles
from playwright.async_api import async_playwright

import uuid
import logging
from datetime import datetime

# Generate a unique runID and datetime string
run_id = uuid.uuid4()
start_time = datetime.now().strftime('%Y%m%d_%H%M%S')

# Configure logging to save to a file
log_filename = f'logs/run_{run_id}_{start_time}.log'
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)


async def setup_browser(playwright):
    """Launch the browser and return the browser instance & a new page."""
    logging.info("Launching browser...")
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--disable-blink-features=AutomationControlled']
    )

    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        extra_http_headers={
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.cuny.edu/',
        },
        viewport=None
    )

    page = await context.new_page()
    page.set_default_timeout(60000)  # 60 seconds timeout

    return browser, context, page  # Return browser & context to keep it open


async def get_colleges(playwright, filter=None):
    """Fetch all college checkboxes and return their details."""
    browser, context, page = await setup_browser(playwright)
    await page.goto("https://globalsearch.cuny.edu/CFGlobalSearchTool/search.jsp", wait_until="networkidle")
    logging.info("Navigated to CUNY Global Search Tool")

    checkboxes = page.locator('ul.checkboxes input[type="checkbox"]')
    colleges = []

    for i in range(await checkboxes.count() - 1):  # Skip the last - "Select All"
        checkbox = checkboxes.nth(i)
        checkbox_id = await checkbox.get_attribute('id')
        label = page.locator(f'label[for="{checkbox_id}"]')
        college_name = await label.inner_text()
        colleges.append({'id': checkbox_id, 'name': college_name})

    # TODO: add option to filter which colleges by seeing which match in filter using regex
    logging.info(f"Colleges: {[college['name'] for college in colleges]}")

    # Select the college
    college = colleges[0]
    college_checkbox = page.locator(f'label[for="{college["id"]}"]')
    await college_checkbox.click()

    term_dropdown = page.get_by_label('Term')
    term_options = await term_dropdown.locator('option').all()  # fall, summer, spring
    term_months = {1: 3, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 2, 9: 1, 10: 1, 11: 1, 12: 1}
    term_option = term_options[term_months[datetime.now().month]]
    value = await term_option.get_attribute('value')
    await term_dropdown.select_option(value)  # Select current term
    term_name = await term_option.inner_text()

    # if term folder not created for current term, create it
    if not os.path.exists(f'schedules/{term_name}'): os.makedirs(f'schedules/{term_name}')

    term = {'dropdown': term_dropdown, 'options': term_options, 'name': term_name, 'value': value}

    return colleges, term


async def process_college(playwright, college, term, semaphore, terms_filter=None):
    """Configure search settings for a specific college."""
    async with semaphore:
        browser, context, page = await setup_browser(playwright)
        await page.goto("https://globalsearch.cuny.edu/CFGlobalSearchTool/search.jsp", wait_until="networkidle")
        logging.info("Navigated to CUNY Global Search Tool")

        # Select the college and term
        college_checkbox = page.locator(f'label[for="{college["id"]}"]')
        await college_checkbox.click()
        college_name = college['name']
        term_dropdown, term_options, value, term = term['dropdown'], term['options'], term['value'], term['name']
        await term_dropdown.select_option(value)  # Select current term
        next_button = page.get_by_role("button", name="Next")
        await next_button.click()
        logging.info(f"{college_name} {term}")

        # Configure search parameters
        slider = page.locator(".slider").first
        await slider.click()
        modalities = ["HyFlex", "Hybrid Synchronous", "In Person", "Hybrid Asynchronous"]
        for modality in modalities:
            modality_checkbox = page.get_by_role("listitem").filter(has_text=modality).locator("span")
            await modality_checkbox.click()
        logging.info(f"Configured search {college_name} {term}")

        # Loop through all the subjects
        subject_dropdown = page.get_by_label('Subject')
        subject_options = await subject_dropdown.locator('option').all()
        if len(subject_options) == 1:  # Skip if no subjects found
            logging.info(f"No subjects found for {college_name} {term}.")
            await page.close()

        for subject_option in subject_options[-2:]:
            await subject_dropdown.select_option(value=await subject_option.get_attribute('value'))
            subject = await subject_option.inner_text()
            logging.info(f"{college_name} {term} {subject}")

            search_button = page.get_by_role("button", name="Search")
            await search_button.click()
            if await page.get_by_text("The search returns no results").is_visible(timeout=6000):
                logging.info(f"No results found for {college_name} {term} {subject}")
                continue

            # Expand all sections
            sections = await page.query_selector_all('[aria-label="Class Section"]')
            for section in sections:
                await section.click()
            expands_course = await page.query_selector_all('[aria-label="Class Section Sub"]')
            for course in expands_course:
                await course.click()
            logging.info('All sections expanded.')

            # Extract table rows for the course
            tables = await page.locator("form[name=\"form_search\"] table").locator("tbody tr").all()
            logging.info(f"Found {len(tables)} courses for {college_name} {term} {subject}")
            schedule_entries = []
            for table in tables:
                cells = table.locator('td')
                courseCode = await cells.nth(0).evaluate("cell => cell.innerText")
                daysAndTimes = await cells.nth(2).evaluate("cell => cell.innerHTML")
                daysAndTimes = daysAndTimes.split('<br>')
                rooms = await cells.nth(3).evaluate("cell => cell.innerHTML")
                rooms = rooms.split('<br>')
                dates = await cells.nth(6).evaluate("cell => cell.innerHTML")
                dates = dates.split('<br>')
                courseName = await cells.nth(8).evaluate("cell => cell.innerText")
                if len(rooms) < len(daysAndTimes): rooms = [rooms[0]] * len(daysAndTimes)

                # filter out TBA and - in dayTimes and rooms
                for j in range(len(daysAndTimes)):
                    if (daysAndTimes[j] in ('TBA', '- ')) or (rooms[j] == 'TBA'): continue
                    try:
                        days, start_time, _, end_time = daysAndTimes[j].split(' ')
                    except ValueError:
                        logging.error(f"Error parsing days and times: {daysAndTimes[j]}")
                        logging.error(f"{college_name} {term} {subject} {courseCode} {courseName}")
                        continue
                    start_date, _, end_date = dates[j].split(' ')

                    entry = {
                        'course_code': courseCode,
                        'course_name': courseName,
                        'room': rooms[j],
                        'days': days,
                        'start_time': start_time,
                        'end_time': end_time,
                        'start_date': start_date,
                        'end_date': end_date,
                    }
                    schedule_entries.append(entry)
                #logging.info(f"Extracted {college_name} {term} {subject} {courseCode} {courseName}")

            async with aiofiles.open(f'schedules/{term}/{college_name}.csv', 'a') as f:
                for entry in schedule_entries:
                    await f.write(f"{college},{term},{subject},{entry['course_code']},{entry['course_name']},{entry['room']},{entry['start_date']},{entry['end_date']},{entry['days']},{entry['start_time']},{entry['end_time']}\n")
            logging.info(f"Added {len(schedule_entries)} entries for {college_name} {term} {subject} {courseCode} {courseName}.")

            # Go back to course selection page
            modify_search_button = page.get_by_role("button", name="Modify Search")
            await modify_search_button.click()
            next_button = page.get_by_role("button", name="Next")
            await next_button.click()
            logging.info(f"Finished {college_name} {term} {subject}.")

        # go back to term selection page
        logging.info(f"Finished {college_name} {term}.")
        await page.close()


async def extract():
    """Main function to extract data for all colleges asynchronously."""
    async with async_playwright() as playwright:
        colleges, term = await get_colleges(playwright)  # Get college list

        semaphore = asyncio.Semaphore(4) # limit concurrent browser instances
        tasks = [
            process_college(playwright, college, term, semaphore)
            for college in colleges
        ]
        await asyncio.gather(*tasks)
        logging.info("Scraping completed.")


if __name__ == "__main__":
    asyncio.run(extract())
