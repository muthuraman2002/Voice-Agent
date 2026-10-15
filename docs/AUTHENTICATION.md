# Authentication System Documentation

## Overview

The Voice Agent platform now includes a comprehensive authentication system with:

- **User Registration & Email Verification**
- **Password-based Login with JWT tokens**
- **OTP-based Login (Magic Link style)**
- **Two-Factor Authentication (TOTP)**
- **Refresh Token System**
- **Password Reset Flow**
- **Plan-based Access Control (Free, Plus, Pro)**
- **Guest Mode (Try without sign-up)**

## User Plans & Restrictions

### Plan Tiers

| Plan | Voice Requests | Features |
|------|----------------|----------|
| Free | 10 requests/day | Basic voice processing |
| Plus | 100 requests/day | Enhanced features |
| Pro | Unlimited | All features, no limits |
| Trial | 100 total requests | One-time trial for free users |
| Guest | 5 total requests | Try without sign-up (24h expiry) |

### Guest Mode (Try Without Sign-up)

Guest mode allows users to try the service without creating an account:

- **No sign-up required** - Start using immediately
- **5 free requests** - Limited to 5 total voice requests
- **24-hour expiry** - Guest sessions expire after 24 hours
- **Anonymous** - No personal information required
- **Easy upgrade** - Sign up anytime to continue

**Use Case**: Perfect for quick testing or first-time users who want to try before committing to sign-up.

### Trial Feature

Free plan users can start a trial that gives them **100 total voice requests** (not daily limits). This allows users to fully test the service before upgrading.

- Trial is available only to free plan users
- Trial counts total requests (not daily)
- Once trial is exhausted, user must upgrade to Plus or Pro
- Trial can only be started once per user

### Plan Hierarchy

```
Free (level 0) → Plus (level 1) → Pro (level 2)
```

Higher tier plans have access to all lower tier features. Trial is an add-on for free users.

## Authentication Endpoints

### Registration

```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "jwt_token_here",
  "refresh_token": "refresh_token_here",
  "token_type": "bearer",
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "two_factor_enabled": false,
    "plan": "free",
    "trial_enabled": false,
    "daily_limit": 10,
    "used_today": 0
  },
  "email_verification_required": true,
  "verification_token": "token_in_dev_mode"
}
```

### Email Verification

```http
POST /api/auth/verify-email
Content-Type: application/json

{
  "token": "verification_token_from_email"
}
```

**Response:**
```json
{
  "message": "Email verified successfully",
  "email_verified": true
}
```

### Resend Verification

```http
POST /api/auth/resend-verification
Authorization: Bearer {access_token}
```

### Password Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (no 2FA):**
```json
{
  "access_token": "jwt_token_here",
  "refresh_token": "refresh_token_here",
  "token_type": "bearer",
  "user": { ... }
}
```

**Response (with 2FA):**
```json
{
  "requires_two_factor": true,
  "login_token": "pending_2fa_token"
}
```

**Response (email not verified):**
```json
{
  "requires_email_verification": true,
  "login_token": "pending_verification_token"
}
```

### Complete Email Verification During Login

```http
POST /api/auth/login/complete-verification
Content-Type: application/json

{
  "token": "pending_verification_token"
}
```

### Two-Factor Authentication (TOTP)

#### Setup 2FA

```http
POST /api/auth/2fa/setup
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "otpauth_uri": "otpauth://totp/VoiceGPT:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=VoiceGPT"
}
```

#### Confirm 2FA

```http
POST /api/auth/2fa/confirm
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "code": "123456"
}
```

#### Disable 2FA

```http
POST /api/auth/2fa/disable
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "code": "123456"
}
```

#### Complete 2FA Login

```http
POST /api/auth/login/2fa
Content-Type: application/json

{
  "login_token": "pending_2fa_token",
  "code": "123456"
}
```

### OTP Login (Magic Link Style)

#### Request OTP

```http
POST /api/auth/login/otp/request
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "If an account exists, a sign-in code has been sent",
  "development_otp": "123456"
}
```

#### Verify OTP

```http
POST /api/auth/login/otp/verify
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456",
  "totp_code": "654321"
}
```

Note: `totp_code` is only required if 2FA is enabled.

### Refresh Token

```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "refresh_token_here"
}
```

**Response:**
```json
{
  "access_token": "new_jwt_token",
  "token_type": "bearer"
}
```

### Logout

```http
POST /api/auth/logout
Content-Type: application/json

{
  "refresh_token": "refresh_token_here"
}
```

### Password Reset

#### Request Reset

```http
POST /api/auth/password-reset/request
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "If an account exists, a password reset link has been sent",
  "reset_token": "token_in_dev_mode"
}
```

#### Confirm Reset

```http
POST /api/auth/password-reset/confirm
Content-Type: application/json

{
  "token": "reset_token",
  "new_password": "newsecurepassword123"
}
```

### Current User Info

```http
GET /api/auth/me
Authorization: Bearer {access_token}
```

**Response (regular plan):**
```json
{
  "id": "user_id",
  "email": "user@example.com",
  "two_factor_enabled": true,
  "plan": "plus",
  "trial_enabled": false,
  "daily_limit": 100,
  "used_today": 5
}
```

**Response (trial active):**
```json
{
  "id": "user_id",
  "email": "user@example.com",
  "two_factor_enabled": false,
  "plan": "free",
  "trial_enabled": true,
  "trial_requests_used": 25,
  "trial_requests_limit": 100,
  "trial_remaining": 75,
  "trial_start_date": "2026-10-15T10:30:00+00:00"
}
```

### Plan Management (Admin Only)

```http
POST /api/auth/admin/plan
Authorization: Bearer {admin_access_token}
Content-Type: application/json

{
  "email": "user@example.com",
  "plan": "pro"
}
```

### Start Trial

Free plan users can start a trial to get 100 total voice requests:

```http
POST /api/auth/start-trial
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "message": "Trial started successfully",
  "trial_requests_limit": 100,
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "two_factor_enabled": false,
    "plan": "free",
    "trial_enabled": true,
    "trial_requests_used": 0,
    "trial_requests_limit": 100,
    "trial_remaining": 100,
    "trial_start_date": "2026-10-15T10:30:00+00:00"
  }
}
```

**Error Responses:**
- `400 Bad Request` - Trial already started
- `400 Bad Request` - Trial only available for free plan users

### Guest Mode (Try Without Sign-up)

Start a guest session to try the service without creating an account:

```http
POST /api/auth/guest/start
```

**Response:**
```json
{
  "message": "Guest session started",
  "session_id": "guest_session_id",
  "access_token": "guest_token_here",
  "token_type": "bearer",
  "guest": true,
  "requests_limit": 5,
  "expires_in_hours": 24
}
```

Use the `access_token` like a regular JWT token to access voice endpoints:

```http
POST /api/voice/process
Authorization: Bearer {guest_token}
Content-Type: multipart/form-data

{
  "audio": <audio_file>
}
```

**Response includes guest status:**
```json
{
  "transcript": "Hello",
  "response": "Hi there!",
  "audio_url": "/static/audio/...",
  "guest": true
}
```

### Guest Session Status

Check guest session status:

```http
GET /api/auth/guest/status
Authorization: Bearer {guest_token}
```

**Response (guest):**
```json
{
  "authenticated": true,
  "guest": true,
  "session_id": "guest_session_id",
  "requests_used": 2,
  "requests_limit": 5,
  "requests_remaining": 3,
  "expires_at": "2026-10-16T10:30:00+00:00"
}
```

**Response (authenticated user):**
```json
{
  "authenticated": true,
  "guest": false,
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "plan": "free",
    "trial_enabled": false,
    "daily_limit": 10,
    "used_today": 5
  }
}
```

## Protected Endpoints by Plan

### Free Tier
```http
GET /api/auth/protected/free
Authorization: Bearer {access_token}
```
Accessible to all users (Free, Plus, Pro).

### Plus Tier
```http
GET /api/auth/protected/plus
Authorization: Bearer {access_token}
```
Accessible to Plus and Pro users only.

### Pro Tier
```http
GET /api/auth/protected/pro
Authorization: Bearer {access_token}
```
Accessible to Pro users only.

### Email Verified Only
```http
GET /api/auth/protected/verified
Authorization: Bearer {access_token}
```
Accessible to users with verified email addresses.

## Using Plan Restrictions in Your Code

```python
from app.core.auth import require_plan, require_email_verification

# Require minimum plan level
@router.get("/api/feature/premium")
async def premium_feature(user: User = Depends(require_plan("plus"))):
    return {"message": "Premium feature accessible"}

# Require email verification
@router.get("/api/feature/verified-only")
async def verified_feature(user: User = Depends(require_email_verification)):
    return {"message": "Verified users only"}

# Combine multiple requirements
@router.get("/api/feature/pro-verified")
async def pro_verified_feature(
    user: User = Depends(require_plan("pro")),
    verified_user: User = Depends(require_email_verification)
):
    return {"message": "Pro and verified"}
```

## Environment Configuration

Add these to your `.env` file:

```bash
# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Verification
EMAIL_VERIFICATION_REQUIRED=true
EMAIL_FROM=noreply@voiceagent.com
EMAIL_VERIFICATION_EXPIRE_HOURS=24

# Password Reset
PASSWORD_RESET_EXPIRE_HOURS=1

# Guest Mode
GUEST_REQUESTS_LIMIT=5

# OTP Configuration
OTP_EXPIRE_MINUTES=10
OTP_EXPOSE_IN_RESPONSE=true  # Set to false in production

# Admin Emails (comma-separated)
ADMIN_EMAILS=admin@example.com,superadmin@example.com
```

## Database Schema

### Users Table
- `id`: UUID (primary key)
- `email`: Email address (unique, indexed)
- `password_hash`: Hashed password
- `plan`: User plan (free, plus, pro)
- `totp_secret`: TOTP secret for 2FA
- `pending_totp_secret`: Pending TOTP secret during setup
- `totp_enabled`: Boolean flag for 2FA status
- `email_verified`: Boolean flag for email verification
- `email_verification_token`: Token for email verification
- `password_reset_token`: Token for password reset
- `password_reset_expires`: Expiration for reset token
- `trial_enabled`: Boolean flag for trial status
- `trial_start_date`: Date when trial started
- `trial_requests_used`: Number of trial requests used
- `trial_requests_limit`: Total trial requests allowed (default: 100)
- `created_at`: Timestamp

### Login OTPs Table
- `id`: UUID (primary key)
- `user_id`: Foreign key to users
- `code_hash`: Hashed OTP code
- `expires_at`: Expiration timestamp
- `used`: Boolean flag

### Guest Sessions Table
- `id`: UUID (primary key)
- `session_token`: Hashed session token (unique, indexed)
- `requests_used`: Number of requests used in this session
- `requests_limit`: Total requests allowed for guest (default: 5)
- `created_at`: Session creation timestamp
- `expires_at`: Session expiration timestamp (24 hours)

### Refresh Tokens Table
- `id`: UUID (primary key)
- `user_id`: Foreign key to users
- `token_hash`: Hashed refresh token
- `expires_at`: Expiration timestamp
- `created_at`: Creation timestamp

### Daily Usage Table
- `id`: UUID (primary key)
- `user_id`: Foreign key to users
- `usage_date`: Date of usage
- `request_count`: Number of requests made

## Trial Feature Details

### How Trial Works

The trial system allows free plan users to test the service with 100 total voice requests before upgrading:

1. **Trial Availability**: Only free plan users can start a trial
2. **Request Counting**: Trial counts total requests (not daily limits like regular plans)
3. **One-Time Use**: Each user can only start a trial once
4. **Trial Expiration**: Once all 100 requests are used, trial is exhausted
5. **Upgrade Path**: After trial exhaustion, user must upgrade to Plus or Pro

### Trial vs Regular Plans

| Feature | Trial | Free Plan | Plus Plan | Pro Plan |
|---------|-------|-----------|-----------|----------|
| Total Requests | 100 (one-time) | 10/day | 100/day | Unlimited |
| Request Type | Total count | Daily limit | Daily limit | No limit |
| Availability | Free users only | All users | Paid users | Paid users |
| Renewal | No | Daily | Daily | N/A |

## Guest Mode Details

### How Guest Mode Works

Guest mode allows users to try the service without creating an account:

1. **No Registration Required**: Users can start immediately without sign-up
2. **Limited Requests**: 5 total voice requests per guest session
3. **Session Expiry**: Guest sessions expire after 24 hours
4. **Anonymous**: No personal information is collected
5. **Easy Upgrade**: Users can sign up anytime to continue

### Guest vs User Accounts

| Feature | Guest Mode | Free Account | Plus Account | Pro Account |
|---------|-----------|--------------|--------------|-------------|
| Sign-up Required | No | Yes | Yes | Yes |
| Total Requests | 5 (one-time) | 10/day | 100/day | Unlimited |
| Session Duration | 24 hours | Permanent | Permanent | Permanent |
| Email Required | No | Yes | Yes | Yes |
| Features | Basic | Basic | Enhanced | All |
| Data Persistence | No | Yes | Yes | Yes |

### Guest Mode Flow

```
Visit Sign-up Page
        ↓
Click "Try" Button
        ↓
Create Guest Session
        ↓
Use Service (5 requests)
        ↓
Session Expires or Requests Exhausted
        ↓
Sign Up to Continue
```

### Guest Mode Use Cases

- **Quick Testing**: Users want to test the service quickly without commitment
- **First Impression**: Allow users to experience the service before signing up
- **Anonymous Access**: Users who prefer not to share personal information initially
- **Conversion Funnel**: Low-friction entry point to convert users to registered accounts

### Frontend Implementation

Add a "Try" button to your sign-up page:

```javascript
// Start guest session
async function startGuestSession() {
  try {
    const response = await fetch('/api/auth/guest/start', {
      method: 'POST',
    });
    const data = await response.json();

    // Store the guest token
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('guest', 'true');

    // Redirect to main app
    window.location.href = '/app';
  } catch (error) {
    console.error('Failed to start guest session:', error);
  }
}

// Check session status
async function checkSessionStatus() {
  const token = localStorage.getItem('access_token');
  if (!token) return null;

  const response = await fetch('/api/auth/guest/status', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return await response.json();
}

// Make authenticated requests (works for both users and guests)
async function makeVoiceRequest(audioFile) {
  const token = localStorage.getItem('access_token');
  const formData = new FormData();
  formData.append('audio', audioFile);

  const response = await fetch('/api/voice/process', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

  const data = await response.json();
  // Response includes 'guest: true' if guest session
  return data;
}
```

**Sign-up Page Example:**

```html
<div class="auth-container">
  <button onclick="startGuestSession()" class="try-button">
    Try for Free (No Sign-up Required)
  </button>

  <div class="divider">or</div>

  <form onsubmit="handleSignUp(event)">
    <input type="email" placeholder="Email" required />
    <input type="password" placeholder="Password" required />
    <button type="submit">Sign Up</button>
  </form>
</div>
```

### Trial Flow

```
User Registration → Free Plan (10/day)
                ↓
          Start Trial (optional)
                ↓
        Trial Active (100 total)
                ↓
        Trial Exhausted
                ↓
        Upgrade to Plus/Pro
```

### Trial Usage Tracking

When a user has an active trial:
- Each voice request increments `trial_requests_used`
- Usage summary shows trial-specific information
- Trial requests are not subject to daily limits
- Once `trial_requests_used >= trial_requests_limit`, trial is exhausted

## Security Best Practices

1. **Change JWT Secret**: Use a strong, random secret in production
2. **Disable OTP Exposure**: Set `OTP_EXPOSE_IN_RESPONSE=false` in production
3. **Email Delivery**: Configure email service (SendGrid, SES, etc.) for verification emails
4. **HTTPS Only**: Always use HTTPS in production
5. **Token Storage**: Store refresh tokens securely (httpOnly cookies recommended)
6. **Rate Limiting**: Implement rate limiting on authentication endpoints
7. **Password Requirements**: Enforce strong password policies
8. **2FA Recommendation**: Encourage users to enable 2FA
9. **Trial Abuse Prevention**: Monitor for trial abuse and implement safeguards

## Development Mode

In development mode, verification tokens and OTP codes are exposed in API responses:

```json
{
  "verification_token": "dev_token_here",
  "development_otp": "123456",
  "reset_token": "reset_token_here"
}
```

In production, these are sent via email/SMS and should not be exposed.

## Next Steps for Production

1. **Email Service Integration**: Integrate with SendGrid, AWS SES, or similar
2. **SMS Service Integration**: For OTP delivery via SMS (Twilio, etc.)
3. **Frontend Integration**: Build login/signup UI with all auth flows
4. **Session Management**: Implement httpOnly cookie-based refresh tokens
5. **Monitoring**: Add logging for authentication events
6. **Audit Trail**: Track login attempts, password changes, etc.
