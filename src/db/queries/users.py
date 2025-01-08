class UserQueries:
    CREATE_USER = """
        INSERT INTO users (phone)
        VALUES ($1)
        RETURNING id, phone, created_at;
    """

    GET_USER_BY_PHONE = """
        SELECT id, phone, created_at, last_login
        FROM users
        WHERE phone = $1;
    """

    CREATE_OTP = """
        INSERT INTO otp_requests (phone, otp, expires_at)
        VALUES ($1, $2, NOW() + INTERVAL '5 minutes')
        RETURNING id;
    """

    VERIFY_OTP = """
        UPDATE otp_requests
        SET verified = true
        WHERE phone = $1 AND otp = $2 
        AND expires_at > NOW() 
        AND verified = false
        RETURNING id;
    """
