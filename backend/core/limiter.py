from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

LIMIT_AUTH_LOGIN = "10/15minutes"
LIMIT_AUTH_SIGNUP = "5/hour"
LIMIT_DEBATE_START = "5/hour"
LIMIT_REPORT_DOWNLOAD = "30/hour"
LIMIT_HEALTH = "60/minute"