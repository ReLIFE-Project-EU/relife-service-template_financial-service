# ReLIFE Service API Template

## Introduction

This is a Python template for a ReLIFE Service API that integrates with Supabase for database operations and storage, and with Keycloak for authentication and authorisation. It provides a foundation for building ReLIFE Services including Supabase user authentication, Keycloak role-based access control, and file storage capabilities.

## Technology Stack

- **Python 3+**: Core programming language
- **FastAPI**: Web framework for building APIs with automatic OpenAPI documentation
- **Uvicorn**: ASGI server for running the FastAPI application
- **Pydantic**: Data validation and settings management using Python type annotations
- **Supabase**: Backend-as-a-Service providing database operations and storage
- **Keycloak**: Identity and access management for authentication and authorization
- **HTTPX**: HTTP client library for making requests
- **Rich**: Terminal output formatting and styling
- **Pytest**: Testing framework with async support

## Configuration

All configuration is driven by environment variables:

| Category     | Variable                 | Description                                       | Default Value                                        |
| ------------ | ------------------------ | ------------------------------------------------- | ---------------------------------------------------- |
| **Server**   | `API_HOST`               | Host address for the API server                   | `0.0.0.0`                                            |
|              | `API_PORT`               | Port for the API server                           | `9090`                                               |
| **Supabase** | `SUPABASE_URL`           | URL of the Supabase instance                      | -                                                    |
|              | `SUPABASE_KEY`           | Service role key with admin privileges            | -                                                    |
| **Keycloak** | `KEYCLOAK_CLIENT_ID`     | Client ID for the application in Keycloak         | -                                                    |
|              | `KEYCLOAK_CLIENT_SECRET` | Client secret for the application in Keycloak     | -                                                    |
|              | `KEYCLOAK_REALM_URL`     | Base URL of the Keycloak realm for authentication | `https://relife-identity.test.ctic.es/realms/relife` |
| **Roles**    | `ADMIN_ROLE_NAME`        | Name of the admin role used for permission checks | `relife_admin`                                       |
| **Storage**  | `BUCKET_NAME`            | Name of the default storage bucket in Supabase    | `default_relife_bucket`                              |

> [!WARNING]
> * The `SUPABASE_KEY` uses the service role key that bypasses Row Level Security (RLS) policies. This should **never** be exposed to clients.
> * `KEYCLOAK_CLIENT_SECRET` is sensitive and should be properly secured in production environments.