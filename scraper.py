import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
import json

# Conditional selenium imports for deployment compatibility
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Selenium not available - using requests fallback only")

class BEUResultScraper:
    def __init__(self):
        self.base_url = 'https://results.beup.ac.in/'
        self.session = requests.Session()
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        if not SELENIUM_AVAILABLE:
            print("Selenium not available, skipping WebDriver setup")
            return False
            
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Try to install and use ChromeDriver
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                print("Chrome WebDriver initialized successfully")
                return self.driver
            except Exception as e:
                print(f"ChromeDriverManager failed: {e}")
                
                # Fallback: try system Chrome driver
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                    print("Using system Chrome WebDriver")
                    return self.driver
                except Exception as e2:
                    print(f"System Chrome driver failed: {e2}")
                    raise Exception(f"Could not initialize Chrome WebDriver: {e2}")
                    
        except Exception as e:
            print(f"WebDriver setup failed: {e}")
            raise e
    
    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def get_available_result_links(self, admission_year=None, publication_dates=None):
        """Get all available B.Tech result links from homepage using requests fallback"""
        try:
            # Try WebDriver first, fallback to requests if it fails
            try:
                if SELENIUM_AVAILABLE and not self.driver:
                    self.setup_driver()
                
                if self.driver:
                    self.driver.get(self.base_url)
                    time.sleep(3)
                    page_source = self.driver.page_source
                    print("Using WebDriver to fetch page")
                else:
                    raise Exception("WebDriver not available")
            except Exception as driver_error:
                print(f"WebDriver failed, using requests fallback: {driver_error}")
                # Fallback to requests
                response = self.session.get(self.base_url)
                page_source = response.text
                print("Using requests to fetch page")
            
            soup = BeautifulSoup(page_source, 'html.parser')
            btech_links = []
            
            # Find all table rows
            rows = soup.find_all('tr')
            print(f"Found {len(rows)} table rows")
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    exam_name = cells[0].get_text().strip()
                    batch_session = cells[1].get_text().strip()
                    published_date = cells[2].get_text().strip()
                    
                    # Check if it's a B.Tech result
                    if 'B.Tech' in exam_name and 'Semester' in exam_name:
                        # Extract semester information
                        semester_match = re.search(r'(\d+)(?:st|nd|rd|th)\s+Semester', exam_name)
                        
                        if semester_match:
                            semester = int(semester_match.group(1))
                            
                            # Extract year from exam name
                            year_match = re.search(r'(\d{4})', exam_name)
                            year = int(year_match.group(1)) if year_match else 2024
                            
                            # Check if it's a special examination
                            is_special = 'Special' in exam_name or '(S)' in exam_name or 'Arrear' in batch_session
                            
                            # Extract admission year from batch_session (e.g., "2021-25" means admission year 2021)
                            batch_admission_year = None
                            if '-' in batch_session and not 'Arrear' in batch_session:
                                try:
                                    batch_start = batch_session.split('-')[0]
                                    if len(batch_start) == 4:
                                        batch_admission_year = int(batch_start)
                                    elif len(batch_start) == 2:
                                        # Convert 2-digit to 4-digit year (21 -> 2021)
                                        batch_admission_year = 2000 + int(batch_start)
                                except:
                                    pass
                            
                            # Filter by admission year if provided
                            include_link = True
                            if admission_year and batch_admission_year:
                                include_link = (batch_admission_year == admission_year)
                            
                            # Filter by publication dates if provided
                            if include_link and publication_dates and published_date:
                                try:
                                    pub_date_obj = datetime.strptime(published_date, '%d-%m-%Y')
                                    pub_date_str = pub_date_obj.strftime('%Y-%m-%d')
                                    include_link = pub_date_str in publication_dates
                                except:
                                    include_link = True
                            
                            if include_link:
                                # Find the corresponding clickable link element (only if using WebDriver)
                                link_element = None
                                href = None
                                
                                if self.driver:
                                    try:
                                        links = self.driver.find_elements(By.TAG_NAME, "a")
                                        for link in links:
                                            if exam_name.strip() in link.text.strip():
                                                link_element = link
                                                href = link.get_attribute('href')
                                                break
                                    except:
                                        pass
                                else:
                                    # For requests fallback, find href from soup
                                    link_tags = soup.find_all('a')
                                    for link_tag in link_tags:
                                        if exam_name.strip() in link_tag.get_text().strip():
                                            href = link_tag.get('href')
                                            if href and not href.startswith('http'):
                                                href = self.base_url + href.lstrip('/')
                                            break
                                
                                btech_links.append({
                                    'text': exam_name,
                                    'semester': semester,
                                    'year': year,
                                    'batch_session': batch_session,
                                    'batch_admission_year': batch_admission_year,
                                    'published_date': published_date,
                                    'is_special': is_special,
                                    'element': link_element,
                                    'href': href
                                })
            
            print(f"Found {len(btech_links)} B.Tech result links")
            return btech_links
            
        except Exception as e:
            print(f"Error getting result links: {e}")
            return []
    
    def navigate_to_semester_results(self, semester_link):
        """Navigate to semester results page using multiple methods"""
        if not SELENIUM_AVAILABLE or not self.driver:
            print("WebDriver not available for navigation")
            return False
            
        try:
            success = False
            
            # Method 1: Direct URL navigation if href is available
            if semester_link.get('href') and 'http' in semester_link['href']:
                try:
                    self.driver.get(semester_link['href'])
                    success = True
                except:
                    pass
            
            # Method 2: Click the element if available
            if not success and semester_link.get('element'):
                try:
                    element = semester_link['element']
                    # Scroll to element first
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)
                    # Click using JavaScript
                    self.driver.execute_script("arguments[0].click();", element)
                    success = True
                except:
                    pass
            
            # Method 3: Execute postback if available
            if not success and semester_link.get('href'):
                try:
                    href = semester_link['href']
                    if 'doPostBack' in href:
                        postback_match = re.search(r"doPostBack\('([^']+)','([^']*)'\)", href)
                        target = postback_match.group(1)
                        argument = postback_match.group(2)
                        script = f"__doPostBack('{target}','{argument}')"
                        self.driver.execute_script(script)
                        success = True
                except:
                    pass
            
            if success:
                time.sleep(3)  # Wait for page to load
                return True
            else:
                print(f"Failed to navigate to semester results: {semester_link['text']}")
                return False
                
        except Exception as e:
            print(f"Error navigating to semester results: {e}")
            return False
    
    def search_student_result(self, registration_number):
        """Search for a specific student's result"""
        if not SELENIUM_AVAILABLE or not self.driver:
            print("WebDriver not available for student search")
            return False
            
        try:
            # Look for registration number input field with various possible names/ids
            possible_selectors = [
                "//input[contains(@name, 'reg')]",
                "//input[contains(@id, 'reg')]",
                "//input[contains(@name, 'RegNo')]",
                "//input[contains(@id, 'RegNo')]",
                "//input[contains(@name, 'txtRegNo')]",
                "//input[contains(@id, 'txtRegNo')]",
                "//input[@type='text']"
            ]
            
            reg_input = None
            for selector in possible_selectors:
                reg_inputs = self.driver.find_elements(By.XPATH, selector)
                if reg_inputs:
                    reg_input = reg_inputs[0]
                    break
            
            if reg_input:
                # Clear and enter registration number
                reg_input.clear()
                reg_input.send_keys(registration_number)
                
                # Look for submit button with various possible texts
                submit_selectors = [
                    "//input[@type='submit']",
                    "//button[@type='submit']",
                    "//button[contains(text(), 'Submit')]",
                    "//button[contains(text(), 'Search')]",
                    "//button[contains(text(), 'Get')]",
                    "//button[contains(text(), 'Show')]",
                    "//input[@value='Submit']",
                    "//input[@value='Search']",
                    "//input[@value='Get Result']"
                ]
                
                submit_button = None
                for selector in submit_selectors:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    if buttons:
                        submit_button = buttons[0]
                        break
                
                if submit_button:
                    # Click submit button
                    self.driver.execute_script("arguments[0].click();", submit_button)
                    
                    # Wait for result to load
                    if SELENIUM_AVAILABLE:
                        WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    time.sleep(3)
                    
                    return True
                else:
                    # Try pressing Enter if no submit button found
                    if SELENIUM_AVAILABLE:
                        reg_input.send_keys(Keys.RETURN)
                    time.sleep(3)
                    return True
            
            return False
        except Exception as e:
            print(f"Error searching for student {registration_number}: {e}")
            return False
    
    def extract_student_result(self, registration_number):
        """Extract student result data from the current page"""
        try:
            result_data = {
                'registration_number': registration_number,
                'name': '',
                'semester': '',
                'year': '',
                'subjects': {},
                'sgpa': '',
                'cgpa': '',
                'result': '',
                'error': None
            }
            
            if not SELENIUM_AVAILABLE or not self.driver:
                print("WebDriver not available for result extraction")
                result_data['error'] = 'WebDriver not available'
                return result_data
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Debug: Save page source for inspection
            print(f"DEBUG: Extracting data for {registration_number}")
            
            # Save page source to file for debugging
            debug_filename = f"debug_page_{registration_number}.html"
            try:
                with open(debug_filename, 'w', encoding='utf-8') as f:
                    f.write(page_source)
                print(f"DEBUG: Saved page source to {debug_filename}")
            except Exception as e:
                print(f"DEBUG: Could not save page source: {e}")
            
            # Look for student name with multiple patterns
            name_patterns = [
                r'Name\s*:?\s*([A-Za-z\s]+)',
                r'Student\s*Name\s*:?\s*([A-Za-z\s]+)',
                r'NAME\s*:?\s*([A-Za-z\s]+)',
                r'Name of Student\s*:?\s*([A-Za-z\s]+)'
            ]
            
            for pattern in name_patterns:
                name_match = re.search(pattern, page_source, re.IGNORECASE)
                if name_match:
                    result_data['name'] = name_match.group(1).strip()
                    print(f"DEBUG: Found name: {result_data['name']}")
                    break
            
            # Also try to find name in table cells
            if not result_data['name']:
                name_cells = soup.find_all('td', string=re.compile(r'Name|NAME', re.IGNORECASE))
                for cell in name_cells:
                    next_cell = cell.find_next_sibling('td')
                    if next_cell:
                        name_text = next_cell.get_text().strip()
                        if name_text and len(name_text) > 2 and not name_text.isdigit():
                            result_data['name'] = name_text
                            print(f"DEBUG: Found name in table: {result_data['name']}")
                            break
            
            # Look for result tables
            tables = soup.find_all('table')
            print(f"DEBUG: Found {len(tables)} tables")
            
            for i, table in enumerate(tables):
                print(f"DEBUG: Processing table {i+1}")
                rows = table.find_all('tr')
                
                for row_idx, row in enumerate(rows):
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) >= 3:
                        # Get all cell texts
                        cell_texts = [cell.get_text().strip() for cell in cells]
                        
                        # Skip header rows and unwanted information
                        row_text = ' '.join(cell_texts).lower()
                        
                        # Skip if it contains header keywords
                        if any(header in row_text for header in ['subject', 'code', 'sl', 'sr', 'paper', 'name', 'father', 'mother', 'college', 'course', 'registration']):
                            continue
                        
                        # Skip if it contains personal/institutional information
                        if any(info in row_text for info in ['kumar', 'devi', 'engineering', 'college', 'computer science', 'sasaram', 'rohtas']):
                            continue
                        
                        # Try to identify actual subject rows
                        first_cell = cell_texts[0]
                        
                        # Check if first cell looks like a proper subject code/name
                        # Subject codes are typically numeric or alphanumeric (like "101", "CS101", "MATH201")
                        # Subject names are typically academic subjects
                        if first_cell and len(first_cell) > 1:
                            # Skip if it looks like personal information
                            if any(word in first_cell.lower() for word in ['name', 'father', 'mother', 'college', 'course', 'registration']):
                                continue
                            
                            # Only process if it looks like a subject (has numeric marks or grades in the row)
                            has_marks = False
                            has_grade = False
                            marks = ''
                            grade = ''
                            
                            for cell_text in cell_texts[1:]:
                                # Check if it's a numeric mark (typically 0-100)
                                if re.match(r'^\d{1,3}$', cell_text) and 0 <= int(cell_text) <= 100:
                                    marks = cell_text
                                    has_marks = True
                                
                                # Check if it's a grade (A, B, C, D, F with optional + or -)
                                if re.match(r'^[A-F][+-]?$', cell_text):
                                    grade = cell_text
                                    has_grade = True
                            
                            # Only add if it has actual academic data (marks or grades)
                            if has_marks or has_grade:
                                # Clean subject name (remove extra whitespace and numbers at start if it's just a serial number)
                                subject_name = first_cell.strip()
                                if re.match(r'^\d+$', subject_name):
                                    # If first cell is just a number, try to get subject name from second cell
                                    if len(cell_texts) > 1 and cell_texts[1].strip():
                                        subject_name = cell_texts[1].strip()
                                
                                result_data['subjects'][subject_name] = {
                                    'marks': marks,
                                    'grade': grade
                                }
                                print(f"DEBUG: Found subject: {subject_name}, marks: {marks}, grade: {grade}")
            
            print(f"DEBUG: Total subjects found: {len(result_data['subjects'])}")
            
            # Extract SGPA from the bottom section (as shown in screenshot)
            # Look for SGPA in various formats
            sgpa_patterns = [
                r'SGPA\s*:?\s*([0-9.]+)',
                r'S\.G\.P\.A\s*:?\s*([0-9.]+)',
                r'Semester\s+Grade\s+Point\s+Average\s*:?\s*([0-9.]+)'
            ]
            
            for pattern in sgpa_patterns:
                sgpa_match = re.search(pattern, page_source, re.IGNORECASE)
                if sgpa_match:
                    result_data['sgpa'] = sgpa_match.group(1)
                    print(f"DEBUG: Found SGPA with regex: {result_data['sgpa']}")
                    break
            
            # Also look for SGPA in table cells (bottom right area)
            if not result_data['sgpa']:
                # Find tables and look for SGPA values
                for table in tables:
                    sgpa_cells = table.find_all('td', string=re.compile(r'SGPA', re.IGNORECASE))
                    for cell in sgpa_cells:
                        # Look for numeric value in the same row or adjacent cells
                        parent_row = cell.find_parent('tr')
                        if parent_row:
                            row_cells = parent_row.find_all('td')
                            for row_cell in row_cells:
                                cell_text = row_cell.get_text().strip()
                                if re.match(r'^[0-9]+\.[0-9]+$', cell_text):
                                    result_data['sgpa'] = cell_text
                                    print(f"DEBUG: Found SGPA in table cell: {result_data['sgpa']}")
                                    break
                        if result_data['sgpa']:
                            break
                    if result_data['sgpa']:
                        break
            
            # Extract CGPA from semester table (Cur. CGPA column as shown in screenshot)
            cgpa_found = False
            
            # Look for "Cur. CGPA" or "Current CGPA" in table headers
            for table in tables:
                header_row = table.find('tr')
                if header_row:
                    headers = header_row.find_all(['th', 'td'])
                    cgpa_col_index = -1
                    
                    # Find the column index for CGPA
                    for i, header in enumerate(headers):
                        header_text = header.get_text().strip()
                        if re.search(r'Cur\.?\s*CGPA|Current\s*CGPA|CGPA', header_text, re.IGNORECASE):
                            cgpa_col_index = i
                            print(f"DEBUG: Found CGPA column at index {i}: {header_text}")
                            break
                    
                    # If CGPA column found, get the value from data rows
                    if cgpa_col_index >= 0:
                        data_rows = table.find_all('tr')[1:]  # Skip header row
                        for row in data_rows:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) > cgpa_col_index:
                                cgpa_text = cells[cgpa_col_index].get_text().strip()
                                if re.match(r'^[0-9]+\.[0-9]+$', cgpa_text):
                                    result_data['cgpa'] = cgpa_text
                                    print(f"DEBUG: Found CGPA in semester table: {result_data['cgpa']}")
                                    cgpa_found = True
                                    break
                        if cgpa_found:
                            break
            
            # Fallback: Look for CGPA with regex patterns
            if not result_data['cgpa']:
                cgpa_patterns = [
                    r'CGPA\s*:?\s*([0-9.]+)',
                    r'C\.G\.P\.A\s*:?\s*([0-9.]+)',
                    r'Cumulative\s+Grade\s+Point\s+Average\s*:?\s*([0-9.]+)'
                ]
                
                for pattern in cgpa_patterns:
                    cgpa_match = re.search(pattern, page_source, re.IGNORECASE)
                    if cgpa_match:
                        result_data['cgpa'] = cgpa_match.group(1)
                        print(f"DEBUG: Found CGPA with regex: {result_data['cgpa']}")
                        break
            
            # Look for overall result
            result_patterns = [
                r'Result\s*:?\s*(PASS|FAIL|PROMOTED)',
                r'Status\s*:?\s*(PASS|FAIL|PROMOTED)'
            ]
            
            for pattern in result_patterns:
                result_match = re.search(pattern, page_source, re.IGNORECASE)
                if result_match:
                    result_data['result'] = result_match.group(1).upper()
                    print(f"DEBUG: Found result: {result_data['result']}")
                    break
            
            # If no explicit result found, determine from SGPA
            if not result_data['result'] and result_data['sgpa']:
                try:
                    sgpa_val = float(result_data['sgpa'])
                    result_data['result'] = 'PASS' if sgpa_val >= 4.0 else 'FAIL'
                except:
                    result_data['result'] = 'UNKNOWN'
            
            # Check if no result found (student doesn't exist)
            if not result_data['subjects'] and not result_data['name']:
                error_indicators = ['not found', 'invalid', 'error', 'no record']
                page_text = page_source.lower()
                
                for indicator in error_indicators:
                    if indicator in page_text:
                        result_data['error'] = f"No result found for registration number {registration_number}"
                        break
            
            print(f"DEBUG: Final result data: name={result_data['name']}, subjects={len(result_data['subjects'])}, sgpa={result_data['sgpa']}, cgpa={result_data['cgpa']}")
            return result_data
            
        except Exception as e:
            print(f"Error extracting result for {registration_number}: {e}")
            return {
                'registration_number': registration_number,
                'name': '',
                'semester': '',
                'year': '',
                'subjects': {},
                'sgpa': '',
                'cgpa': '',
                'result': '',
                'error': str(e)
            }
    
    def scrape_semester_results(self, semester_link, registration_numbers, progress_callback=None):
        """Scrape results for multiple students in a semester"""
        results = []
        
        try:
            # Navigate to semester results page
            if not self.navigate_to_semester_results(semester_link):
                return results
            
            total_students = len(registration_numbers)
            
            for i, reg_number in enumerate(registration_numbers):
                try:
                    if progress_callback:
                        progress = ((i + 1) / total_students) * 100
                        progress_callback(progress, f"Processing student {reg_number}")
                    
                    # Search for student result
                    if self.search_student_result(reg_number):
                        result = self.extract_student_result(reg_number)
                        result['semester'] = semester_link['semester']
                        result['year'] = semester_link['year']
                        results.append(result)
                    else:
                        # Student not found
                        results.append({
                            'registration_number': reg_number,
                            'semester': semester_link['semester'],
                            'year': semester_link['year'],
                            'error': 'Could not search for student result'
                        })
                    
                    # Go back to search page for next student
                    if SELENIUM_AVAILABLE and self.driver:
                        self.driver.back()
                        time.sleep(1)
                    
                except Exception as e:
                    print(f"Error processing student {reg_number}: {e}")
                    results.append({
                        'registration_number': reg_number,
                        'semester': semester_link['semester'],
                        'year': semester_link['year'],
                        'error': str(e)
                    })
                    
                    # Try to go back to search page
                    try:
                        if SELENIUM_AVAILABLE and self.driver:
                            self.driver.back()
                            time.sleep(1)
                    except:
                        # Re-navigate to semester page if back fails
                        self.navigate_to_semester_results(semester_link)
            
            return results
            
        except Exception as e:
            print(f"Error scraping semester results: {e}")
            return results
    
    def scrape_multiple_semesters(self, semester_links, registration_numbers, admission_year=None, progress_callback=None):
        """Scrape results for multiple semesters with homepage return between each"""
        all_results = []
        
        try:
            total_semesters = len(semester_links)
            
            for i, semester_link in enumerate(semester_links):
                if progress_callback:
                    semester_progress = (i / total_semesters) * 100
                    progress_callback(semester_progress, f"Processing Semester {semester_link['semester']} ({semester_link['batch_session']})")
                
                print(f"\n--- Processing Semester {semester_link['semester']} ---")
                print(f"Exam: {semester_link['text']}")
                print(f"Batch: {semester_link['batch_session']}")
                print(f"Published: {semester_link['published_date']}")
                
                # Go back to homepage before each semester
                print("Returning to homepage...")
                if SELENIUM_AVAILABLE and self.driver:
                    self.driver.get(self.base_url)
                    time.sleep(3)
                
                # Get fresh links with admission year filter
                fresh_links = self.get_available_result_links(admission_year)
                
                # Find exact matching link based on text and batch
                matching_link = None
                for link in fresh_links:
                    if (link['text'] == semester_link['text'] and 
                        link['batch_session'] == semester_link['batch_session']):
                        matching_link = link
                        break
                
                if matching_link:
                    print(f"Found matching link: {matching_link['text']}")
                    semester_results = self.scrape_semester_results(
                        matching_link, 
                        registration_numbers,
                        progress_callback
                    )
                    all_results.extend(semester_results)
                    print(f"Scraped {len(semester_results)} results for this semester")
                else:
                    print(f"Could not find matching link for: {semester_link['text']} ({semester_link['batch_session']})")
                    # Add error entry for this semester
                    for reg_num in registration_numbers:
                        all_results.append({
                            'registration_number': reg_num,
                            'semester': semester_link['semester'],
                            'year': semester_link['year'],
                            'batch_session': semester_link['batch_session'],
                            'error': f"Semester link not found: {semester_link['text']}"
                        })
            
            return all_results
            
        except Exception as e:
            print(f"Error scraping multiple semesters: {e}")
            return all_results
    
    def generate_registration_numbers(self, admission_year, branch_code, start_num, end_num):
        """Generate registration numbers based on the format YYBBBCCCNNN"""
        reg_numbers = []
        year_suffix = str(admission_year)[-2:]  # Get last 2 digits of year
        college_code = '124'  # Constant college code
        
        for num in range(int(start_num), int(end_num) + 1):
            student_id = f"{num:03d}"  # 3-digit padded
            reg_number = f"{year_suffix}{branch_code}{college_code}{student_id}"
            reg_numbers.append(reg_number)
        
        return reg_numbers
