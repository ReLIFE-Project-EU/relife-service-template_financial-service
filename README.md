# ReLIFE Service API Template

## Configuration

All configuration is driven by environment variables:

| Category     | Variable                 | Description                                       | Default Value           |
| ------------ | ------------------------ | ------------------------------------------------- | ----------------------- |
| **Server**   | `API_HOST`               | Host address for the API server                   | `0.0.0.0`               |
|              | `API_PORT`               | Port for the API server                           | `9090`                  |
| **Supabase** | `SUPABASE_URL`           | URL of the Supabase instance                      | -                       |
|              | `SUPABASE_KEY`           | Service role key with admin privileges            | -                       |
| **Keycloak** | `KEYCLOAK_CLIENT_ID`     | Client ID for the application in Keycloak         | -                       |
|              | `KEYCLOAK_CLIENT_SECRET` | Client secret for the application in Keycloak     | -                       |
| **Roles**    | `ADMIN_ROLE_NAME`        | Name of the admin role used for permission checks | `relife_admin`          |
| **Storage**  | `BUCKET_NAME`            | Name of the default storage bucket in Supabase    | `default_relife_bucket` |

> [!WARNING]
> * The `SUPABASE_KEY` uses the service role key that bypasses Row Level Security (RLS) policies. This should **never** be exposed to clients.
> * `KEYCLOAK_CLIENT_SECRET` is sensitive and should be properly secured in production environments.