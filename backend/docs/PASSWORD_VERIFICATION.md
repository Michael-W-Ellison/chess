# Password Verification and Security Guide

This document explains the password verification, validation, and security features of the parent dashboard authentication system.

## Overview

The Chess Tutor application includes comprehensive password verification features to ensure strong password security:

- **Password strength validation** - Enforces minimum security requirements
- **Rate limiting** - Prevents brute force attacks
- **Password change** - Secure password update workflow
- **Initial setup** - First-time password configuration
- **Common password detection** - Blocks weak, commonly-used passwords

## Password Requirements

All passwords must meet the following requirements:

✅ **Minimum 8 characters long**
✅ **At least one uppercase letter** (A-Z)
✅ **At least one lowercase letter** (a-z)
✅ **At least one digit** (0-9)
✅ **At least one special character** (!@#$%^&*()_+-=[]{}|;:,.<>?)
✅ **Not a common password** (e.g., "password123", "admin")

### Password Strength Levels

Passwords are rated as:
- **Weak** - Meets minimum requirements only (score ≤ 3)
- **Medium** - Good variety and length (score 4-5)
- **Strong** - Excellent variety and length (score ≥ 6)

Strength is calculated based on:
- Length (8+, 12+, 16+ characters)
- Character variety (lowercase, uppercase, digits, specials)

## Security Features

### 1. Rate Limiting

**Protection against brute force attacks:**
- Maximum **5 failed login attempts**
- **15-minute lockout** after limit reached
- Automatic cleanup of old attempts
- Clear error messages with remaining attempts

**Example Error Messages:**
```
"Invalid password. 3 attempts remaining."
"Too many failed attempts. Account locked for 12 minutes."
```

### 2. Password Validation

**Real-time password checking:**
- Validates against all requirements
- Calculates strength score
- Detects common passwords
- Provides detailed error messages

**Validation Response:**
```json
{
  "valid": false,
  "errors": [
    "Password must contain at least one uppercase letter",
    "Password must contain at least one digit"
  ],
  "strength": "weak"
}
```

### 3. Common Password Detection

**Rejects commonly-used passwords:**
- "password", "password123", "12345678"
- "qwerty", "abc123", "admin"
- "chess", "parent", "letmein"
- And many more...

### 4. Bcrypt Password Hashing

**Secure password storage:**
- 12 rounds of bcrypt hashing
- No plaintext passwords stored
- Timing attack resistant
- Industry-standard security

## API Endpoints

### Get Password Requirements

```bash
GET /api/parent/auth/requirements
```

**Response:**
```json
{
  "requirements": "Password must contain:\n- At least 8 characters long\n- At least one uppercase letter (A-Z)\n- ...",
  "min_length": 8,
  "requires": {
    "uppercase": true,
    "lowercase": true,
    "digit": true,
    "special": true
  }
}
```

### Validate Password Strength

Test password without saving it:

```bash
POST /api/parent/auth/validate-password
Content-Type: application/json

{
  "password": "TestPass123!"
}
```

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "strength": "strong"
}
```

### Initial Password Setup

For first-time configuration when no password is set:

```bash
POST /api/parent/auth/setup-password
Content-Type: application/json

{
  "password": "MySecurePass123!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Password setup complete",
  "password_hash": "$2b$12$abcd1234...",
  "jwt_secret": "abc123def456...",
  "instructions": "Add these to your .env file:\nPARENT_DASHBOARD_PASSWORD=$2b$12$abcd1234...\nJWT_SECRET_KEY=abc123def456...\nThen restart the server."
}
```

**Steps:**
1. Call setup endpoint with desired password
2. Copy `password_hash` and `jwt_secret` from response
3. Add to `.env` file as instructed
4. Restart backend server

### Change Password

Update password (requires authentication):

```bash
POST /api/parent/auth/change-password
Authorization: Bearer <your-token>
Content-Type: application/json

{
  "current_password": "OldPass123!",
  "new_password": "NewSecurePass456!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Password changed successfully",
  "new_password_hash": "$2b$12$xyz789...",
  "instructions": "Update PARENT_DASHBOARD_PASSWORD in your .env file with the new hash and restart the server"
}
```

**Steps:**
1. Call endpoint with current and new passwords
2. Copy `new_password_hash` from response
3. Update `PARENT_DASHBOARD_PASSWORD` in `.env`
4. Restart backend server
5. Login with new password

### Enhanced Login (with Rate Limiting)

Login includes rate limiting and detailed error messages:

```bash
POST /api/parent/auth/login
Content-Type: application/json

{
  "password": "YourPassword123!"
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 28800
}
```

**Error Responses:**

**Invalid Password (401):**
```json
{
  "detail": "Invalid password. 3 attempts remaining."
}
```

**Rate Limited (429):**
```json
{
  "detail": "Too many login attempts. Please try again in 12 minutes."
}
```

**Not Configured (403):**
```json
{
  "detail": "Authentication not properly configured. Please set PARENT_DASHBOARD_PASSWORD and JWT_SECRET_KEY."
}
```

## Usage Examples

### Frontend Password Validation

**React Example:**

```javascript
import { useState } from 'react';

function PasswordInput({ value, onChange }) {
    const [validation, setValidation] = useState(null);

    const validatePassword = async (password) => {
        const response = await fetch('/api/parent/auth/validate-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });
        const result = await response.json();
        setValidation(result);
    };

    const handleChange = (e) => {
        const newPassword = e.target.value;
        onChange(newPassword);
        validatePassword(newPassword);
    };

    return (
        <div>
            <input
                type="password"
                value={value}
                onChange={handleChange}
                placeholder="Enter password"
            />
            {validation && (
                <div>
                    <div>Strength: {validation.strength}</div>
                    {validation.errors.map((error, i) => (
                        <div key={i} style={{ color: 'red' }}>{error}</div>
                    ))}
                </div>
            )}
        </div>
    );
}
```

### Initial Setup Workflow

**Step 1: Check if password is configured**

```javascript
const checkSetup = async () => {
    const response = await fetch('/api/parent/auth/status');
    const { required, configured } = await response.json();

    if (required && !configured) {
        // Show password setup form
        return 'needs_setup';
    }
    // Show login form
    return 'login';
};
```

**Step 2: Setup password**

```javascript
const setupPassword = async (password) => {
    // Validate first
    const validationResponse = await fetch('/api/parent/auth/validate-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
    });

    const validation = await validationResponse.json();
    if (!validation.valid) {
        alert(`Password issues: ${validation.errors.join(', ')}`);
        return;
    }

    // Setup password
    const setupResponse = await fetch('/api/parent/auth/setup-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
    });

    const setup = await setupResponse.json();

    // Display instructions to user
    alert(setup.instructions);
};
```

### Password Change Workflow

```javascript
const changePassword = async (currentPassword, newPassword, token) => {
    // Validate new password first
    const validationResponse = await fetch('/api/parent/auth/validate-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: newPassword })
    });

    const validation = await validationResponse.json();
    if (!validation.valid) {
        alert(`Password issues: ${validation.errors.join(', ')}`);
        return;
    }

    // Change password
    const response = await fetch('/api/parent/auth/change-password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword
        })
    });

    if (response.ok) {
        const result = await response.json();
        alert(result.instructions);
    } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
    }
};
```

### Handling Rate Limiting

```javascript
const handleLogin = async (password) => {
    try {
        const response = await fetch('/api/parent/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });

        if (response.status === 429) {
            const error = await response.json();
            // Show lockout message
            alert(error.detail); // "Too many attempts. Try again in 12 minutes."
            return;
        }

        if (response.status === 401) {
            const error = await response.json();
            // Show remaining attempts
            alert(error.detail); // "Invalid password. 3 attempts remaining."
            return;
        }

        if (response.ok) {
            const { access_token } = await response.json();
            // Store token and redirect
            localStorage.setItem('auth_token', access_token);
            window.location.href = '/dashboard';
        }

    } catch (error) {
        console.error('Login error:', error);
    }
};
```

## Security Best Practices

### For Users

1. **Choose Strong Passwords**
   - Use password manager to generate secure passwords
   - Aim for 16+ characters
   - Include mix of all character types

2. **Unique Passwords**
   - Don't reuse passwords from other services
   - Avoid common patterns or dictionary words

3. **Regular Updates**
   - Change password periodically
   - Change immediately if compromised

4. **Secure Storage**
   - Store password in password manager
   - Don't write password down
   - Don't share password

### For Developers

1. **Never Log Passwords**
   - Log failed attempts, not password values
   - Sanitize logs of sensitive data

2. **Secure Configuration**
   - Never commit `.env` with passwords
   - Use environment variables in production
   - Rotate JWT secrets regularly

3. **HTTPS Only**
   - Always use HTTPS in production
   - Never transmit passwords over HTTP
   - Consider secure, httpOnly cookies

4. **Monitor Failed Attempts**
   - Log all authentication failures
   - Monitor for unusual patterns
   - Alert on repeated lockouts

## Troubleshooting

### Password Validation Failures

**Problem:** "Password must contain at least one uppercase letter"

**Solution:** Add at least one capital letter (A-Z)

**Problem:** "Password is too common"

**Solution:** Choose a more unique password, avoid common words

**Problem:** "Password must be at least 8 characters long"

**Solution:** Make password longer (recommend 12-16 characters)

### Rate Limiting Issues

**Problem:** "Too many login attempts"

**Solution:** Wait for lockout period (15 minutes) or restart backend to reset

**Development Tip:** Restart backend server to clear rate limit attempts during testing

### Password Change Issues

**Problem:** "Current password is incorrect"

**Solution:** Verify you're entering the correct current password

**Problem:** "New password must be different from current password"

**Solution:** Choose a different password

## Password Manager Utility

Use the command-line utility for password management:

```bash
cd backend
python utils/password_manager.py
```

**Options:**
1. Generate new password and hash
2. Hash an existing password
3. Generate JWT secret key
4. Verify password against hash

This is the recommended way to generate secure passwords and hashes.

## Summary

The password verification system provides:

✅ Strong password requirements
✅ Real-time validation feedback
✅ Rate limiting against brute force
✅ Secure password change workflow
✅ Initial setup assistance
✅ Common password detection
✅ bcrypt hashing security
✅ Comprehensive error messages

All passwords are validated before hashing, rate limited during login, and securely stored. The system is designed to be both secure and user-friendly.
