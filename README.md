# LIINE Take Home Test - Restaurant Hours API

The project consists of a FastAPI application that provides opening hours information for  
restaurants based on provided datetime queries.

## Requirements

- **FastAPI**
- **Uvicorn**
- **Python-DateUtil**

## Features

- **RESTful API**: Clean, well-documented REST endpoints
- **Flexible DateTime Parsing**: Supports multiple datetime formats
- **Comprehensive Coverage**: Handles complex restaurant hours including overnight periods
- **Robust Error Handling**: Graceful error responses with helpful messages
- **Docker Support**: Fully containerized with Docker and docker-compose
- **Comprehensive Testing**: Unit tests and integration tests

## Environment Configuration

The application uses environment variables for configuration. You can set these in multiple ways:

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `RESTAURANTS_CSV_FILE` | Path to the restaurant data CSV file | `restaurants.csv` | No |
| `PORT` | API server port | `8000` | No |
| `HOST` | API server host | `0.0.0.0` | No |


### Fallback Behavior

The application has smart fallbacks:
- If `RESTAURANTS_CSV_FILE` is not set → it will use `restaurants.csv` in the current directory
- If the CSV file doesn't exist → the app will start but return 'service unavailable' for queries
- Docker volume mount provides an additional fallback at `/app/restaurants.csv`

## Installation and Run Instructions
### Initial Setup
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd liine_gerald_guerrero
   ```

2. **Set up environment (optional)**:  
   set up .env based on provided .env.example
   ```bash
   cp .env.example .env
   # Edit .env file if you need custom settings such as file location for the csv
   ```
   or set environment variables directly
   ```bash
   # Set directly in your shell
   export RESTAURANTS_CSV_FILE=/path/to/restaurants.csv
   ```

    ### Fallback Behavior

    The application has smart fallbacks:
    - If `RESTAURANTS_CSV_FILE` is not set → it will use `restaurants.csv` in the current directory
    - If the CSV file doesn't exist → the app will start but returns 'service unavailable' for queries
    - Docker volume mount provides an additional fallback at `/app/restaurants.csv`


### Run Option 1: Docker (Recommended)

1. **Run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

2. **Access the API**:
   - API Documentation: http://localhost:8000
   - Health Check: http://localhost:8000/health

### Run Option 2: Local Development

1. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   uvicorn liine_gerald_guerrero.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Run tests**:
   ```bash
   pytest tests/ -v
   ```

## API Endpoints

### 1. Find Open Restaurants
**GET** `/restaurants/open`

Find restaurants that are open at a specific datetime.

**Parameters**:
- `datetime` (required): DateTime string in various formats

**Supported DateTime Formats**:
The API accepts datetime strings in multiple formats

- **ISO Format**: `2023-12-25T15:30:00`
- **ISO Without Seconds**: `2023-12-25T15:30`
- **Space Separated**: `2023-12-25 15:30:00`
- **US Format**: `12/25/2023 3:30 PM`
- **European Format**: `25/12/2023 15:30`
- **Human Readable**: `December 25, 2023 3:30 PM`

**Example Requests**:
```bash
# ISO format
curl "http://localhost:8000/restaurants/open?datetime=2023-12-25T15:30:00"

# Human readable
curl "http://localhost:8000/restaurants/open?datetime=December%2025,%202023%203:30%20PM"

# Simple format
curl "http://localhost:8000/restaurants/open?datetime=2023-12-25%2015:30"
```

**Response**:
```json
{
  "restaurants": ["Restaurant Name 1", "Restaurant Name 2"],
  "query_datetime": "2023-12-25T15:30:00",
  "total_count": 2
}
```

### 2. Health Check
**GET** `/health`

Check API health status and version information.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### 3. Restaurant Count
**GET** `/restaurants/count`

Get total number of loaded restaurants.

**Response**:
```json
{
  "total_restaurants": 41,
  "data_loaded": true
}
```

## Error Handling

The API provides comprehensive error handling:

- **400 Bad Request**: Invalid datetime format
- **422 Unprocessable Entity**: Invalid request parameters
- **500 Internal Server Error**: Unexpected server errors

## Performance Considerations

- **Efficient Parsing**: Restaurant hours are parsed once at startup
- **Fast Lookups**: In-memory data structure for quick queries
- **Async Support**: FastAPI's async capabilities for concurrent requests
- **Docker Optimization**: Multi-stage builds and slim base images for optimised containerization

## Security Features

- **Input Validation**: Pydantic models validate all inputs
- **Error Sanitization**: No sensitive information in error responses
- **Container Security**: Non-root user in Docker container for improved security
- **Dependency Management**: Pinned dependency versions

