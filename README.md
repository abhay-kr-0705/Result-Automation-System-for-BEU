# College Results Automation System

A comprehensive web scraping system for Bihar Engineering University (BEU) B.Tech examination results automation.

## Features

🔹 **Automated Result Scraping**
- Auto-visits and crawls data from https://results.beup.ac.in/
- Scrapes B.Tech examination results only
- Handles multiple semesters and students in batch

🔹 **Smart Registration Number Generation**
- Format: YYBBBCCCNNN
- YY: Year of admission (e.g., 21 for 2021)
- BBB: Branch code (e.g., 110 for EEE)
- CCC: College code (constant 124)
- NNN: Unique student ID (001-999, 3-digit padded)

🔹 **Supported Branches**
- Electronics Engineering (VLSI): 159
- Computer Science & Engineering (CSE): 105
- Electrical & Electronics Engineering (EEE): 110
- Civil Engineering: 101
- Mining Engineering: 113
- Mechanical Engineering: 102

🔹 **Frontend Features**
- Secure login system
- Semester availability based on admission year
- Multi-semester selection
- Registration number range input
- Excel/CSV export functionality
- Real-time progress tracking

## Installation

1. **Clone or download the project**
   ```bash
   cd "C:\Users\abhay\OneDrive\Desktop\Result Automation"
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Chrome WebDriver**
   The system will automatically download and manage Chrome WebDriver using webdriver-manager.

## Usage

1. **Start the application**
   ```bash
   python app.py
   ```

2. **Access the web interface**
   Open your browser and go to: http://localhost:5000

3. **Login**
   - Username: `Result@SEC`
   - Password: `SEC@Result12#`

4. **Configure scraping parameters**
   - Enter year of admission (e.g., 2021)
   - Select branch from dropdown
   - Choose registration number range (e.g., 1 to 30)
   - Select semesters to scrape
   - Optionally set passout year and publication date

5. **Start scraping**
   - Click "Scrape & Download Excel" or "Download as CSV"
   - Wait for the process to complete
   - Download the generated file

## System Architecture

```
├── app.py                 # Main Flask application
├── scraper.py            # Web scraping module using Selenium
├── templates/
│   ├── login.html        # Login page
│   └── dashboard.html    # Main dashboard
├── temp/                 # Temporary files for downloads
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Technical Details

### Web Scraping Process
1. Initialize Chrome WebDriver with headless mode
2. Navigate to BEU results homepage
3. Extract available B.Tech result links
4. For each selected semester:
   - Navigate to semester results page
   - Search for each registration number
   - Extract student data (name, marks, grades, SGPA, CGPA)
   - Handle errors for non-existent students
5. Compile all results into structured format
6. Export to Excel/CSV with proper formatting

### Data Structure
Each student result contains:
- Registration Number
- Student Name
- Semester and Year
- Subject-wise marks and grades
- SGPA/CGPA (if available)
- Overall result (PASS/FAIL)
- Error information (if any)

### Error Handling
- Graceful handling of non-existent registration numbers
- Network timeout and retry mechanisms
- WebDriver cleanup on completion or failure
- Detailed error reporting in output files

## Security Features

- Single account authentication
- Session management
- Secure file handling
- Input validation and sanitization

## Browser Compatibility

- Chrome WebDriver (automatically managed)
- Headless operation for server environments
- Responsive web interface for all modern browsers

## Troubleshooting

### Common Issues

1. **Chrome WebDriver Issues**
   - The system automatically downloads the correct WebDriver version
   - Ensure Chrome browser is installed on the system

2. **Network Connectivity**
   - Verify internet connection
   - Check if BEU results website is accessible

3. **No Results Found**
   - Verify registration number format
   - Check if results are published for the selected semester/year
   - Ensure correct branch code selection

4. **Permission Errors**
   - Run with appropriate file system permissions
   - Ensure temp directory is writable

### Performance Tips

- Use smaller registration number ranges for faster processing
- Select specific semesters instead of all available
- Monitor system resources during large batch operations

## Support

For issues or questions, check the error messages in the web interface or console output for detailed debugging information.

## License

This system is designed for educational and administrative purposes at Bihar Engineering University, Patna.
