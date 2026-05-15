# uData Harvesting System Documentation

## Overview

The uData harvesting system allows you to automatically fetch metadata from remote data sources and import them into your uData instance. This enables you to aggregate datasets from multiple sources, making them searchable and discoverable in a single portal.

## Architecture

### Core Components

1. **HarvestSource**: Represents a remote endpoint to harvest from
2. **HarvestJob**: Tracks the execution of a harvesting operation
3. **HarvestItem**: Represents individual items (datasets/dataservices) being processed
4. **Backend**: Protocol implementation for harvesting from specific data formats
5. **BaseBackend**: Abstract base class that all harvesters must extend

### Key Concepts

- **Backend**: A protocol implementation to harvest a remote endpoint
- **Source**: A remote endpoint to harvest, characterized by a URL and backend implementation
- **Job**: A complete harvesting operation for a given source
- **Validation**: Each harvester must be validated by administrators before running

## Existing Harvesters

### 1. DCAT Backend (`dcat`)

**Purpose**: Harvests datasets from DCAT-compliant endpoints

**Features**:
- Supports DCAT-AP format
- Handles pagination via Hydra ontology
- Processes both datasets and dataservices
- Supports multiple RDF formats (JSON-LD, XML, Turtle, etc.)

**Configuration**:
```python
# Enable in udata.cfg
PLUGINS = ['dcat']
```

**Usage**:
```bash
# Create a DCAT harvester
udata harvest create "My DCAT Source" https://data.example.com/catalog.json dcat
```

**Field Mapping**:

| Dataset Field | DCAT Property | Notes |
|---------------|---------------|-------|
| title | dct:title | |
| description | dct:description | HTML parsed as Markdown |
| tags | dct:keyword + dct:theme | |
| frequency | dct:accrualPeriodicity | |
| temporal_coverage | dct:temporal | See temporal coverage section |
| license | N/A | See license detection section |
| resources | dct:distribution | Also matches dct:distributions |

### 2. CSW-DCAT Backend (`csw-dcat`)

**Purpose**: Harvests from CSW (Catalogue Service for the Web) endpoints that return DCAT

**Features**:
- CSW protocol support
- DCAT format parsing
- Pagination handling

### 3. CSW-ISO-19139 Backend (`csw-iso-19139`)

**Purpose**: Harvests from CSW endpoints returning ISO 19139 metadata, transformed to DCAT

**Features**:
- ISO 19139 metadata support
- XSLT transformation to DCAT-AP
- Geospatial data focus

**Configuration**:
```python
extra_configs = (
    HarvestExtraConfig(
        "Remote URL prefix",
        "remote_url_prefix", 
        str,
        "A prefix used to build the remote URL of the harvested items."
    ),
)
```

### 4. Statistika Backend (`statistika`)

**Purpose**: Harvests from Serbian Statistical Office API

**Features**:
- JSON API integration
- Category-based dataset organization
- Multiple resource formats (JSON, CSV)

**Implementation**:
```python
class StatistikaBackend(BaseBackend):
    display_name = 'Statistika'
    verify_ssl = False

    def inner_harvest(self):
        response = self.get(self.source.url)
        data = response.json()
        
        for item in data:
            self.process_dataset(item['IDkategorija'])
```

### 5. RGZ Backend (`rgz`)

**Purpose**: Harvests from Republicki geodetski zavod (Serbian Geodetic Institute)

**Features**:
- CSW ISO 19139 support
- Geospatial metadata
- Resource normalization

### 6. SDG Backend (`sdg`)

**Purpose**: Harvests Sustainable Development Goals data

**Features**:
- SDG-specific data processing
- Goal and target mapping

## Creating a New Harvester

### Step 1: Extend BaseBackend

All harvesters must extend `udata.harvest.backends.base.BaseBackend` and implement required methods:

```python
from udata.harvest.backends.base import BaseBackend, HarvestFeature, HarvestFilter, HarvestExtraConfig
from udata.models import Dataset, Resource
from udata.i18n import gettext as _

class MyCustomBackend(BaseBackend):
    display_name = "My Custom Harvester"
    
    # Optional: Define features your harvester supports
    features = (
        HarvestFeature(
            'feature_name',
            _('Feature Label'),
            _('Feature description'),
            default=False
        ),
    )
    
    # Optional: Define filters your harvester supports
    filters = (
        HarvestFilter(
            _('Filter Label'),
            'filter_key',
            str,
            _('Filter description')
        ),
    )
    
    # Optional: Define extra configuration options
    extra_configs = (
        HarvestExtraConfig(
            _('API Key'),
            'api_key',
            str,
            _('API key for authentication')
        ),
    )
```

### Step 2: Implement Required Methods

#### `inner_harvest()` Method

This method is responsible for discovering and iterating through all items to harvest:

```python
def inner_harvest(self):
    """Main harvesting logic - discover and process all items"""
    # Fetch data from remote source
    response = self.get(self.source.url)
    data = response.json()
    
    # Store job data for later use
    self.job.data = {
        'response_data': data,
        'processed_items': []
    }
    
    # Iterate through items and process each one
    for item in data['datasets']:
        remote_id = item['id']
        self.process_dataset(remote_id, item_data=item)
        
        # Check if we've reached the maximum items limit
        if self.is_done():
            break
```

#### `inner_process_dataset()` Method

This method processes a single dataset:

```python
def inner_process_dataset(self, item: HarvestItem, **kwargs):
    """Process a single dataset"""
    # Get or create the dataset
    dataset = self.get_dataset(item.remote_id)
    
    # Extract data from kwargs or fetch from remote
    item_data = kwargs.get('item_data')
    if not item_data:
        # Fetch individual item if not provided
        response = self.get(f"{self.source.url}/dataset/{item.remote_id}")
        item_data = response.json()
    
    # Map remote data to dataset fields
    dataset.title = item_data.get('title', '')
    dataset.description = item_data.get('description', '')
    dataset.tags = item_data.get('tags', [])
    
    # Process resources
    dataset.resources = []
    for resource_data in item_data.get('resources', []):
        resource = Resource(
            title=resource_data.get('title', ''),
            description=resource_data.get('description', ''),
            url=resource_data.get('url', ''),
            filetype='remote',
            format=resource_data.get('format', ''),
            mime=resource_data.get('mime_type', '')
        )
        dataset.resources.append(resource)
    
    return dataset
```

#### `inner_process_dataservice()` Method (Optional)

If your harvester supports dataservices, implement this method:

```python
def inner_process_dataservice(self, item: HarvestItem, **kwargs):
    """Process a single dataservice"""
    from udata.core.dataservices.models import Dataservice
    
    dataservice = self.get_dataservice(item.remote_id)
    
    # Map remote data to dataservice fields
    item_data = kwargs.get('item_data', {})
    dataservice.title = item_data.get('title', '')
    dataservice.description = item_data.get('description', '')
    
    return dataservice
```

### Step 3: Register Your Harvester

Add your harvester to the entry points in `setup.py`:

```python
setup(
    # ... other setup parameters
    entry_points={
        'udata.harvesters': [
            'my-custom = mypackage.harvest.backends:MyCustomBackend',
        ],
    },
)
```

### Step 4: Enable Your Harvester

Add your harvester to the `PLUGINS` configuration in `udata.cfg`:

```cfg
PLUGINS = ['my-custom']
```

## Advanced Features

### Filters

Filters allow users to configure what data to harvest:

```python
filters = (
    HarvestFilter(
        _('Dataset Type'),
        'dataset_type',
        str,
        _('Filter by dataset type')
    ),
    HarvestFilter(
        _('Date Range'),
        'date_range',
        str,
        _('Filter by date range (YYYY-MM-DD/YYYY-MM-DD)')
    ),
)
```

### Features

Features provide optional capabilities:

```python
features = (
    HarvestFeature(
        'include_resources',
        _('Include Resources'),
        _('Include resource metadata in harvest'),
        default=True
    ),
    HarvestFeature(
        'validate_schema',
        _('Validate Schema'),
        _('Validate data against schema before import'),
        default=False
    ),
)
```

### Extra Configuration

Additional configuration options:

```python
extra_configs = (
    HarvestExtraConfig(
        _('API Key'),
        'api_key',
        str,
        _('API key for authentication')
    ),
    HarvestExtraConfig(
        _('Base URL'),
        'base_url',
        str,
        _('Base URL for API endpoints')
    ),
)
```

## Error Handling

### Custom Exceptions

Use the provided exceptions for proper error handling:

```python
from udata.harvest.exceptions import (
    HarvestException,
    HarvestSkipException,
    HarvestValidationError
)

def inner_process_dataset(self, item: HarvestItem, **kwargs):
    try:
        # Your processing logic
        if not item.remote_id:
            raise HarvestSkipException("Missing identifier")
        
        # Validate data
        if not self.validate_data(data):
            raise HarvestValidationError("Invalid data format")
            
    except HarvestSkipException:
        # Item will be marked as skipped
        raise
    except HarvestValidationError:
        # Item will be marked as failed
        raise
    except Exception as e:
        # Unexpected error - item will be marked as failed
        raise HarvestException(f"Processing failed: {str(e)}")
```

## Testing Your Harvester

### Unit Tests

Create tests for your harvester:

```python
import pytest
from udata.harvest.tests.factories import HarvestSourceFactory
from mypackage.harvest.backends import MyCustomBackend

class TestMyCustomBackend:
    def test_harvest_success(self):
        source = HarvestSourceFactory(
            backend='my-custom',
            url='https://api.example.com/datasets'
        )
        
        backend = MyCustomBackend(source, dryrun=True)
        job = backend.harvest()
        
        assert job.status == 'done'
        assert len(job.items) > 0
        
    def test_process_dataset(self):
        source = HarvestSourceFactory(backend='my-custom')
        backend = MyCustomBackend(source, dryrun=True)
        
        # Create a job first
        backend.job = HarvestJob.objects.create(
            status='initialized',
            source=source
        )
        
        # Test processing a single dataset
        backend.process_dataset('test-id', item_data={'title': 'Test Dataset'})
        
        assert len(backend.job.items) == 1
        assert backend.job.items[0].status == 'done'
```

### Integration Tests

Test with real API endpoints:

```python
def test_real_api_integration(self):
    source = HarvestSourceFactory(
        backend='my-custom',
        url='https://real-api.example.com/datasets'
    )
    
    backend = MyCustomBackend(source, dryrun=True)
    job = backend.harvest()
    
    # Verify job completed successfully
    assert job.status in ['done', 'done-errors']
    
    # Verify items were processed
    assert len(job.items) > 0
    
    # Check for any errors
    failed_items = [item for item in job.items if item.status == 'failed']
    assert len(failed_items) == 0, f"Failed items: {failed_items}"
```

## Best Practices

### 1. Error Handling

- Always handle network errors gracefully
- Provide meaningful error messages
- Use appropriate exception types
- Log errors for debugging

### 2. Performance

- Implement pagination for large datasets
- Use `self.is_done()` to respect `HARVEST_MAX_ITEMS`
- Consider caching responses when appropriate
- Handle timeouts properly

### 3. Data Quality

- Validate data before processing
- Handle missing or malformed data gracefully
- Provide fallbacks for required fields
- Clean and normalize data

### 4. Configuration

- Make your harvester configurable
- Provide sensible defaults
- Document configuration options
- Validate configuration values

### 5. Logging

- Use appropriate log levels
- Include relevant context in log messages
- Don't log sensitive information
- Use structured logging when possible

## Debugging

### Synchronous Execution

For debugging, use the synchronous harvest command:

```bash
udata harvest run <source_id>
```

### Dry Run Mode

Use dry run mode to test without saving data:

```python
backend = MyCustomBackend(source, dryrun=True)
job = backend.harvest()
```

### Log Analysis

Check harvest job logs for errors:

```python
job = HarvestJob.objects.get(id=job_id)
for item in job.items:
    if item.status == 'failed':
        print(f"Failed item {item.remote_id}: {item.errors}")
```

## Command Line Interface

### Available Commands

```bash
# List all harvest sources
udata harvest sources

# List available backends
udata harvest backends

# Create a new harvest source
udata harvest create "Source Name" "https://api.example.com" backend_name

# Run a harvester synchronously
udata harvest run <source_id>

# Launch a harvester asynchronously
udata harvest launch <source_id>

# Validate a source
udata harvest validate <source_id>

# Schedule periodic harvesting
udata harvest schedule <source_id> --frequency daily

# Delete a source
udata harvest delete <source_id>
```

### Configuration Examples

```bash
# Create a DCAT harvester
udata harvest create "Open Data Portal" "https://data.example.com/catalog.json" dcat

# Create a custom harvester with configuration
udata harvest create "My API" "https://api.example.com" my-custom --config '{"api_key": "secret"}'

# Schedule daily harvesting
udata harvest schedule <source_id> --frequency daily --cron "0 2 * * *"
```

## Monitoring and Maintenance

### Job Status Monitoring

Monitor harvest jobs for issues:

```python
from udata.harvest.models import HarvestJob

# Check for failed jobs
failed_jobs = HarvestJob.objects(status='failed')
for job in failed_jobs:
    print(f"Failed job {job.id} for source {job.source.name}")

# Check for jobs with errors
jobs_with_errors = HarvestJob.objects(status='done-errors')
for job in jobs_with_errors:
    print(f"Job {job.id} completed with errors")
```

### Cleanup

Clean up old jobs and archived datasets:

```bash
# Purge old jobs
udata harvest purge

# Clean up archived datasets
udata harvest clean <source_id>
```

## Troubleshooting

### Common Issues

1. **Network Errors**: Check connectivity and API endpoints
2. **Authentication Errors**: Verify API keys and credentials
3. **Data Format Errors**: Validate remote data format
4. **Memory Issues**: Implement pagination for large datasets
5. **Timeout Errors**: Increase timeout settings or implement retry logic

### Debugging Tips

1. Use dry run mode for testing
2. Check job logs for detailed error information
3. Test with small datasets first
4. Validate configuration before running
5. Monitor system resources during harvesting

## Conclusion

The uData harvesting system provides a flexible and extensible framework for importing data from various sources. By following the patterns established in the existing harvesters and implementing the required methods, you can create custom harvesters that integrate seamlessly with the uData platform.

For more information, refer to:
- [Existing harvesters](https://github.com/opendatateam/udata/tree/master/udata/harvest/backends)
- [Cookiecutter template](https://github.com/opendatateam/cookiecutter-udata-harvester)
- [uData documentation](https://udata.readthedocs.io/) 