API_BASE_URL = "https://api.penpencil.co"
STATIC_BASE_URL = "https://static.pw.live"


class AuthURLs:
    GET_OTP = f"{API_BASE_URL}/v1/users/get-otp"
    RESEND_OTP = f"{API_BASE_URL}/v1/users/resend-otp"
    TOKEN = f"{API_BASE_URL}/v3/oauth/token"
    RESET_PASSWORD = f"{API_BASE_URL}/v1/users/reset-password"
    REFRESH_TOKEN = f"{API_BASE_URL}/v3/oauth/refresh-token"
    EXCHANGE_TOKEN = f"{API_BASE_URL}/v3/oauth/exchange-token"
    VERIFY_TOKEN = f"{API_BASE_URL}/v3/oauth/verify-token"
    LOGOUT = f"{API_BASE_URL}/v1/oauth/logout"
    APP_CONSTANTS = f"{STATIC_BASE_URL}/auth-fe/assets/json/app-constants.json"


class BatchURLs:
    GET_BATCHES = f"{API_BASE_URL}/batch-service/v1/batches/purchased-batches"
    BATCH_BASE = f"{API_BASE_URL}/v3/batches/"
