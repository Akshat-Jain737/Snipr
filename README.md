# Snipr

A robust and feature-rich URL shortener service built with Python and FastAPI. This service allows you to shorten long URLs, generate QR codes, and track analytics for each shortened link along with fast redirect.

## Features

- **URL Shortening**: Create short, manageable links from long URLs with support for custom aliases and expiration times.
- **Safety First**: Integrates with the Google Safe Browsing API to prevent the shortening of malicious or unsafe URLs.
- **QR Code Generation**: Instantly generate a QR code for any shortened URL.
- **Detailed Analytics**:
  - Track total and unique clicks.
  - Gather insights on traffic sources with geolocation data (country, region, city).
  - Analyze user demographics (browser, OS, device).
  - Capture and analyze UTM parameters (`utm_source`, `utm_medium`, `utm_campaign`, etc.) for marketing campaigns.
- **High Performance**: Utilizes Redis for caching frequently accessed URLs and for efficient rate limiting, reducing database load and ensuring fast redirects.
- **Asynchronous Tasks**: Background tasks are used for non-critical operations like analytics processing to ensure a fast user experience during redirection.

## Technology Stack

- **Backend Framework**: FastAPI
- **Database ORM**: SQLModel
- **Database**: MySQL
- **Database Migrations**: Alembic
- **Caching & Rate Limiting**: Redis
- **Async HTTP Client**: HTTPX
- **Data Validation**: Pydantic

## Setup and Installation

### Prerequisites
- Python 3.9+
- A running MySQL server
- A running Redis instance
- Google Safe Browsing API Key

### 1. Clone the Repository

```bash
git clone git@github.com:Akshat-Jain737/Snipr.git
cd <repository-directory>
```

### 2. Install Dependencies

It's recommended to use a virtual environment.

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory of the project and add the following variables.

```env
# Database Configuration
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=url_shortener_db

# Google Safe Browsing API
GOOGLE_SAFE_BROWSING_API_KEY=your_google_api_key
```

### 4. Run Database Migrations

Alembic is used to manage database schema changes. Run the following commands to get require schema for this:

```bash
alembic revision --autogenerate -m "intial_migration"
alembic upgrade head
```

This will create all the necessary tables (`url`, `analytics`, `analytics_2`, `utmanalytics`).

### 5. Run the Application

```bash
uvicorn main:app --reload
```

The application will be available at `http://127.0.0.1:8000`.

### 6. Access API Documentation

Once the server is running, you can access the interactive API documentation at `http://127.0.0.1:8000/scalar`.

## API Endpoints

| Method | Endpoint                               | Description                                     |
|--------|----------------------------------------|-------------------------------------------------|
| `POST` | `/url/shorten`                         | Shortens a long URL.                            |
| `GET`  | `/url/{custom_alias}/{short_key}`      | Redirects to the original long URL.             |
| `GET`  | `/url/{custom_alias}/{short_key}/qr`   | Generates a QR code for the short URL.          |
| `GET`  | `/url/{custom_alias}/{short_key}/analytics` | Retrieves detailed analytics for the short URL. |
| `GET`  | `/url/all-urls`                        | Lists all the URLs shortened by the service.    |

## Future Enhancements

This project is under active development. Here are some of the features planned for the near future:

- **Full CRUD for URLs**:
  - **Update**: Implement functionality to edit the destination of a short URL.
  - **Delete**: Add the ability to delete a short URL.

- **Authentication System**:
  - Implement a robust user authentication and authorization system (e.g., using JWTs).

- **Protected Routes & User-Specific URLs**:
  - Once authentication is in place, routes for creating, updating, deleting, and viewing analytics for URLs will be protected.
  - Users will only be able to manage and view analytics for the URLs they have created.
- **Files and Folders structure**:
  - planned to improve files and folders structure
- **Async Codebase**:
  - Refactor synchronous database and caching operations to be fully asynchronous to leverage FastAPI's performance benefits.
  

---

If you encounter any issues or errors while using Snipr, please open an issue here.
