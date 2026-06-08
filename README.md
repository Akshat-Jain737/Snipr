# Snipr

A robust and feature-rich URL shortener service built with Python and FastAPI. This service allows users to shorten long URLs, generate QR codes, and track analytics for each shortened link, all with fast redirects and a secure authentication system.

## Features

- **URL Shortening**: Create short, manageable links from long URLs with support for custom aliases and expiration times.
- **User Authentication**: Secure user registration and login system using JWT (JSON Web Tokens) with access and refresh tokens. Refresh token rotation is implemented for enhanced security.
- **Full URL Management**: Users can update the expiration time of their URLs or delete them entirely.
- **User-Specific Data**:
  - Users can only manage and view analytics for the URLs they have created.
  - List all URLs created by the currently authenticated user.
- **Asynchronous from the Ground Up**: Built with `async` and `await` to be fully asynchronous, leveraging FastAPI's performance benefits for high-concurrency.
- **Safety First**: Integrates with the Google Safe Browsing API to prevent the shortening of malicious or unsafe URLs.
- **QR Code Generation**: Instantly generate a QR code for any shortened URL.
- **Detailed Analytics**:
  - Track total and unique clicks.
  - Gather insights on traffic sources with geolocation data (country, region, city).
  - Analyze user demographics (browser, OS, device).
  - Capture and analyze UTM parameters (`utm_source`, `utm_medium`, `utm_campaign`, etc.) for marketing campaigns.
- **Background Processing**: Analytics data is processed in the background to ensure redirects are as fast as possible.
- **High Performance**: Utilizes Redis for caching frequently accessed URLs and for efficient rate limiting, reducing database load and ensuring fast redirects.

## Technology Stack

- **Backend Framework**: FastAPI
- **Database ORM**: SQLModel
- **Database**: MySQL
- **Database Migrations**: Alembic
- **Caching & Rate Limiting**: Redis
- **Asynchronous Operations**: `asyncio`, `aiomysql`, `redis[asyncio]`, `httpx`
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

# JWT Configuration
JWT_SECRET_KEY=your_super_secret_key_for_jwt
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7


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

| Method | Endpoint                               | Description                                          |
|--------|----------------------------------------|------------------------------------------------------|
| `POST` | `/auth/register`                       | Register a new user.                                 |
| `POST` | `/auth/login`                          | Log in a user and receive JWTs.                      |
| `POST` | `/auth/refresh`                        | Refresh an access token using a refresh token.       |
| `POST` | `/auth/logout`                         | Log out the user by revoking the session.            |
| `POST` | `/snipr/shorten`                       | Shortens a long URL (Authentication required).       |
| `GET`  | `/snipr/all-urls`                      | Lists all URLs for the current user (Auth required). |
| `GET`  | `/snipr/{custom_alias}/{short_key}`    | Redirects to the original long URL.                  |
| `GET`  | `/snipr/{custom_alias}/{short_key}/qr` | Generates a QR code for the short URL.               |
| `GET`  | `/snipr/{custom_alias}/{short_key}/analytics` | Retrieves analytics for a URL (Auth required).       |
| `PATCH`| `/snipr/{short_key}`                   | Updates a short URL's properties (Auth required).    |
| `DELETE`| `/snipr/{short_key}`                  | Deletes a short URL (Auth required).                 |

## Future Enhancements

This project is under active development. Here are some of the features planned for the near future:


- **Enhanced Analytics**:
  - Implement time-series analytics to show click trends over time.

---

If you encounter any issues or errors while using Snipr, please open an issue here.
