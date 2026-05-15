# CSV Export API for Active Users

This document describes the new API endpoint for exporting all active users in CSV format.

## Overview

The API endpoint `/api/1/users/export.csv` allows authorized clients to retrieve a CSV export of all active users in the system. The endpoint is protected by an API key that must be configured in the udata configuration.

## Configuration

### Setting up the API Key

Add the following configuration to your `udata.cfg` file:

```python
# CSV Export API Key - Set this to a long, random string for security
CSV_EXPORT_API_KEY = "your-very-long-random-api-key-here"
```

**Important Security Notes:**
- Use a long, randomly generated string (at least 32 characters)
- Keep this key secret and secure
- Consider rotating the key periodically
- If this key is not set, the endpoint will return a 503 error

### Generating a Secure API Key

You can generate a secure API key using Python:

```python
import secrets
api_key = secrets.token_urlsafe(32)
print(f"CSV_EXPORT_API_KEY = \"{api_key}\"")
```

## API Endpoint

### Endpoint Details

- **URL**: `/api/1/users/export.csv`
- **Method**: `GET`
- **Authentication**: API Key (header or query parameter)
- **Response Format**: CSV file
- **Content-Type**: `text/csv; charset=utf-8`

### Authentication Methods

The API key can be provided in two ways:

#### 1. HTTP Header (Recommended)
```bash
curl -H "X-API-KEY: your-api-key-here" \
     https://your-domain.com/api/1/users/export.csv
```

#### 2. Query Parameter
```bash
curl "https://your-domain.com/api/1/users/export.csv?api-key=your-api-key-here"
```

### Response

#### Success Response (200 OK)
- **Content-Type**: `text/csv; charset=utf-8`
- **Content-Disposition**: `attachment; filename=active-users-YYYY-MM-DD-HH-MM.csv`
- **Body**: CSV data with user information

#### Error Responses

| Status Code | Description | Response Body |
|-------------|-------------|---------------|
| 401 | Invalid or missing API key | `{"message": "Invalid or missing API key"}` |
| 503 | CSV export API key not configured | `{"message": "CSV export API key not configured"}` |

## CSV Format

The CSV export includes the following fields for each active user:

- `id` - User ID
- `slug` - User slug
- `first_name` - User's first name
- `last_name` - User's last name
- `email` - User's email address
- `website` - User's website URL
- `about` - User's description/bio
- `active` - Whether the user is active (always `True` for this export)
- `roles` - User's roles
- `created_at` - User creation timestamp
- `last_login_at` - Last login timestamp
- `current_login_at` - Current login timestamp
- `last_login_ip` - Last login IP address
- `current_login_ip` - Current login IP address
- `login_count` - Number of logins
- `organizations` - Comma-separated list of organization IDs
- `deleted` - Whether the user is deleted (always `False` for this export)
- Additional metric fields (dynamic based on configuration)

## Filtering

The endpoint only returns:
- **Active users** (`active=True`)
- **Non-deleted users** (`deleted=None`)

Inactive and deleted users are automatically excluded from the export.

## Usage Examples

### Using curl
```bash
# Using header authentication
curl -H "X-API-KEY: your-secret-api-key" \
     -o active_users.csv \
     https://your-domain.com/api/1/users/export.csv

# Using query parameter authentication
curl -o active_users.csv \
     "https://your-domain.com/api/1/users/export.csv?api-key=your-secret-api-key"
```

### Using Python requests
```python
import requests

url = "https://your-domain.com/api/1/users/export.csv"
headers = {"X-API-KEY": "your-secret-api-key"}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    with open("active_users.csv", "wb") as f:
        f.write(response.content)
    print("CSV export saved successfully")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### Using JavaScript/fetch
```javascript
const apiKey = "your-secret-api-key";
const url = "https://your-domain.com/api/1/users/export.csv";

fetch(url, {
    headers: {
        "X-API-KEY": apiKey
    }
})
.then(response => {
    if (response.ok) {
        return response.blob();
    }
    throw new Error(`HTTP error! status: ${response.status}`);
})
.then(blob => {
    // Download the CSV file
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = 'active_users.csv';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
})
.catch(error => console.error('Error:', error));
```

## Security Considerations

1. **API Key Storage**: Store the API key securely and never commit it to version control
2. **HTTPS**: Always use HTTPS when calling this endpoint to protect the API key in transit
3. **Access Control**: Limit access to this endpoint to trusted systems and personnel
4. **Key Rotation**: Consider rotating the API key periodically
5. **Monitoring**: Monitor access to this endpoint for suspicious activity
6. **Data Sensitivity**: The exported data contains user information - handle it according to your privacy policies

## Testing

To test the endpoint during development, you can set a test API key in your configuration:

```python
# In your test configuration
CSV_EXPORT_API_KEY = "test-api-key-12345"
```

Then test with:
```bash
curl -H "X-API-KEY: test-api-key-12345" \
     http://localhost:7000/api/1/users/export.csv
```

## Implementation Details

- The endpoint uses the existing `UserCsvAdapter` class for consistent CSV formatting
- Authentication is handled by a custom `csv_api_key_required` decorator
- The endpoint supports both header and query parameter authentication for flexibility
- Only active, non-deleted users are included in the export
- The CSV stream is generated efficiently using the existing CSV streaming infrastructure 