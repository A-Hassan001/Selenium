# Trademarks IPO Gov UK Automation

## Overview

This project automates the process of querying the UK Intellectual Property Office (IPO) Trademarks database to verify trademark registration status for a list of companies. The script processes company names from an input CSV file and outputs comprehensive results indicating whether each company has a registered UK trademark.

## Features

- **Automated Trademark Search**: Queries the official UK IPO trademarks database
- **Batch Processing**: Processes multiple companies from a CSV input file
- **Robust Error Handling**: Implements retry logic with exponential backoff
- **Dual Output Files**: Generates full results and a filtered list of companies without trademarks
- **Session Persistence**: Resumes processing from the last completed entry
- **Detailed Logging**: Comprehensive console and file-based logging for audit trails
- **Undetected Chrome**: Uses undetected-chromedriver to bypass automation detection

## Requirements

- Python 3.7+
- Google Chrome browser
- Windows operating system (for registry-based Chrome version detection)

### Dependencies

Install required packages using:

```bash
pip install -r requirements.txt
```

**Key Dependencies:**
- `selenium==4.43.0` - Web automation framework
- `undetected_chromedriver==3.5.5` - Anti-detection Selenium wrapper

## Project Structure

```
Trademarks IPO Gov UK Automation/
├── input/
│   └── dataset_crawler-google-places.csv
├── output/
│   ├── dataset_crawler-google-places_(full_results).csv
│   ├── dataset_crawler-google-places_(no_trademark_only).csv
│   └── logs/
├── config.json
├── requirements.txt
├── trademarks.py
└── README.md
```

## Configuration

Edit `config.json` to customize the script behavior:

```json
{
  "input_file_name": "dataset_crawler-google-places.csv",
  "target_column_name": "title",
  "search_type": "Exact"
}
```

**Configuration Parameters:**
- `input_file_name`: Name of the input CSV file in the `input/` directory
- `target_column_name`: Column name containing company names to search
- `search_type`: Search query type (`Exact`, `Broad`, etc.)

## Input Format

The input CSV file must contain a column with company names. Example:

```csv
title,totalScore,reviewsCount,street,city
Hazel Court,4.3,437,1 Hazel Ct,York
Rainbow Restoration - York & Yorkshire Coast,5,9,Unit 8 London Ebor Business Park,York
```

## Output Files

### 1. Full Results CSV
**File**: `dataset_crawler-google-places_(full_results).csv`

Contains all processed companies with the following additional column:
- `uk_trademark_registered`: "Yes", "No", or "error"

### 2. No Trademark Only CSV
**File**: `dataset_crawler-google-places_(no_trademark_only).csv`

Filtered list containing only companies without registered UK trademarks:

```csv
companyName,uk_trademark_registered
Company Name A,No
Company Name B,No
```

### 3. Log Files
**Directory**: `logs/`

Timestamped log files containing detailed execution information, errors, and search results.

## Usage

### Basic Execution

```bash
python trademarks.py
```

The script will:
1. Load configuration from `config.json`
2. Read company names from the input CSV
3. Query the UK IPO database for each company
4. Save results to output files
5. Generate detailed logs

### Resume Interrupted Processing

The script automatically tracks processed companies and skips them on subsequent runs. To restart from the beginning, delete or rename the output CSV files.

## Search Logic

The script employs multi-step logic to determine trademark registration:

1. **Primary Check**: Detects `.search-results .grid-row` elements
2. **URL Analysis**: Checks for "result" in the current URL
3. **Error Handling**: Parses error messages for:
   - "No trade marks matching your search criteria were found" → No
   - "More than 1,000 results" → Yes
4. **Retry Mechanism**: Attempts up to 3 retries on failure

## Error Handling & Retries

- **Automatic Retries**: Failed searches are retried up to 3 times
- **Timeout Management**: Search results wait up to 5 minutes for page load
- **Session Recovery**: Automatically refreshes browser session on element not found errors
- **Graceful Degradation**: Logs errors and continues processing

## Logging

**Console Output**: High-level information (INFO level)
**File Output**: Detailed debugging information (DEBUG level)

Log format:
```
[TIMESTAMP] [LEVEL] [MESSAGE]
```

Example:
```
[2024-05-12 14:23:45] INFO [1/100] Company Name
----------------------------------
Trademark Registered: Yes
```

## Technical Specifications

### Browser Automation
- **WebDriver**: Undetected Chrome (bypasses bot detection)
- **Window State**: Maximized
- **Profile Directory**: Local `chrome_profile/` directory

### Search Parameters
- **Target URL**: `https://trademarks.ipo.gov.uk/ipo-tmtext`
- **Search Method**: Dropdown selection from predefined search types
- **Wait Strategy**: Explicit waits with CSS selectors

## Limitations

- **Windows Only**: Registry-based Chrome version detection (requires modification for cross-platform use)
- **Single Browser**: Processes queries sequentially
- **Rate Limiting**: UK IPO may implement rate limiting on repeated queries
- **JavaScript Execution**: Requires page load completion and JavaScript rendering

## Performance Considerations

- Average processing time: 5-15 seconds per company
- Total runtime depends on number of companies and server response times
- Logs consume disk space (~1 MB per 1000 searches)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Chrome not found | Verify Chrome installation; check registry settings |
| Element not found timeout | Increase timeout value in `is_element_exist()` method |
| "No trade marks matching" showing for all searches | Verify internet connection and IPO website availability |
| Script hangs | Check firewall/proxy settings; restart browser session |

## Disclaimer

This automation tool is provided for legitimate business purposes. Users are responsible for complying with the UK IPO's terms of service and applicable laws. The tool should not be used for spam, scraping violations, or other malicious purposes.

## Support & Maintenance

For issues or modifications, refer to the inline code comments and logging output. The script maintains detailed logs in the `logs/` directory for audit and debugging purposes.

## License

This project is maintained by A-Hassan001. For licensing inquiries, contact the repository owner.

---

**Last Updated**: 2026-05-12  
**Version**: 1.0  
**Author**: A-Hassan001
