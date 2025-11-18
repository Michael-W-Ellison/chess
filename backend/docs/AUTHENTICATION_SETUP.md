# Parent Dashboard Authentication Setup Guide

This guide explains how to set up and use password protection for the parent dashboard.

## Overview

The Chess Tutor application includes JWT-based authentication to protect parent dashboard access. When enabled, users must provide a valid password to access parent dashboard endpoints.

## Features

- **Password-based authentication** with bcrypt hashing
- **JWT tokens** for session management
- **Configurable expiration** (default: 8 hours)
- **Optional protection** - can be disabled for development
- **Secure password storage** - only hashed passwords stored
- **Helper utilities** for password management

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs the required authentication libraries:
- `python-jose` - JWT token handling
- `passlib` - Password hashing with bcrypt
- `python-multipart` - Form data parsing

### 2. Generate Passwords and Keys

Use the password manager utility:

```bash
cd backend
python utils/password_manager.py
```

**Select option 1** to generate a new secure password:
```
Generated Password:
  xK9#mP2@vL4$nR6^

Hashed Password (store in .env):
  $2b$12$abcd1234...
```

**Select option 3** to generate a JWT secret key:
```
JWT Secret Key (store in .env):
  abc123def456...
```

### 3. Configure Environment

Add to your `.env` file:

```bash
# Enable password protection
PARENT_DASHBOARD_REQUIRE_PASSWORD=True

# Hashed password (from password manager)
PARENT_DASHBOARD_PASSWORD=$2b$12$abcd1234...

# JWT secret key (from password manager)
JWT_SECRET_KEY=abc123def456...

# Token expiration (optional, default 480 minutes = 8 hours)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480
```

**Important:**
- Never commit `.env` file to version control
- Use the **hashed** password, not the plaintext one
- Keep JWT secret key secure and random

### 4. Start the Backend

```bash
cd backend
python main.py
```

The authentication system is now active!

## Using the Authentication System

### Frontend Integration

#### 1. Check Authentication Status

Before attempting login, check if authentication is required:

```javascript
const response = await fetch('http://localhost:8000/api/parent/auth/status');
const { required, configured } = await response.json();

if (required && !configured) {
    alert('Authentication not configured on server');
}
```

#### 2. Login

Send password to get JWT token:

```javascript
const response = await fetch('http://localhost:8000/api/parent/auth/login', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        password: 'your-password-here'
    })
});

const { access_token, expires_in } = await response.json();

// Store token (localStorage, sessionStorage, or memory)
localStorage.setItem('auth_token', access_token);
```

#### 3. Make Authenticated Requests

Include token in Authorization header:

```javascript
const token = localStorage.getItem('auth_token');

const response = await fetch('http://localhost:8000/api/parent/dashboard/overview?user_id=1', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});

const data = await response.json();
```

#### 4. Handle Authentication Errors

```javascript
if (response.status === 401) {
    // Token expired or invalid - redirect to login
    localStorage.removeItem('auth_token');
    window.location.href = '/login';
}
```

#### 5. Verify Token

Check if token is still valid:

```javascript
const response = await fetch('http://localhost:8000/api/parent/auth/verify', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});

if (response.ok) {
    console.log('Token is valid');
} else {
    console.log('Token expired or invalid');
}
```

### API Testing with curl

#### Login:
```bash
curl -X POST http://localhost:8000/api/parent/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password":"your-password"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 28800
}
```

#### Use Token:
```bash
TOKEN="your-jwt-token-here"

curl http://localhost:8000/api/parent/dashboard/overview?user_id=1 \
  -H "Authorization: Bearer $TOKEN"
```

### API Testing with Python

```python
import requests

# Login
login_response = requests.post(
    'http://localhost:8000/api/parent/auth/login',
    json={'password': 'your-password'}
)
token = login_response.json()['access_token']

# Make authenticated request
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(
    'http://localhost:8000/api/parent/dashboard/overview?user_id=1',
    headers=headers
)
data = response.json()
```

## API Endpoints

### Authentication Endpoints

#### POST /api/parent/auth/login
Login and get JWT token.

**Request:**
```json
{
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 28800
}
```

**Status Codes:**
- `200` - Success
- `401` - Invalid password
- `403` - Authentication not configured

#### GET /api/parent/auth/status
Check authentication requirements.

**Response:**
```json
{
  "authenticated": false,
  "required": true,
  "configured": true
}
```

#### GET /api/parent/auth/verify
Verify token validity (requires authentication).

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "authenticated": true,
  "user": "parent",
  "message": "Token is valid"
}
```

### Protected Endpoints

The following endpoints require authentication when `PARENT_DASHBOARD_REQUIRE_PASSWORD=True`:

- `GET /api/parent/dashboard/overview` - Dashboard overview
- All other `/api/parent/*` endpoints

**Example protected endpoint usage:**
```bash
curl http://localhost:8000/api/parent/dashboard/overview?user_id=1 \
  -H "Authorization: Bearer $TOKEN"
```

## Password Management

### Generate New Password

```bash
cd backend
python utils/password_manager.py
```

Select option 1 or 2 to generate/hash passwords.

### Change Password

1. Generate new hashed password using password manager
2. Update `PARENT_DASHBOARD_PASSWORD` in `.env`
3. Restart backend server
4. All existing tokens remain valid until expiration

### Hash Existing Password

If you already have a password and want to hash it:

```bash
python utils/password_manager.py
# Select option 2
# Enter your password
# Copy the hashed value to .env
```

### Verify Password

Test if a password matches a hash:

```bash
python utils/password_manager.py
# Select option 4
# Enter password and hash
```

## Security Best Practices

### 1. Strong Passwords

- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- Use password manager utility to generate secure passwords
- Don't reuse passwords from other services

### 2. JWT Secret Key

- Use password manager to generate random secret
- Minimum 32 characters
- Never hardcode in source code
- Rotate periodically for production systems

### 3. Token Management

- Store tokens securely (avoid localStorage for sensitive apps)
- Clear tokens on logout
- Implement token refresh for long sessions
- Validate tokens server-side on every request

### 4. HTTPS in Production

- Always use HTTPS in production
- Never send tokens over unencrypted HTTP
- Consider using secure, httpOnly cookies

### 5. Password Storage

- Never store plaintext passwords
- Only store bcrypt hashes
- Never commit `.env` file with secrets

## Disabling Authentication

For development or testing, you can disable authentication:

**.env:**
```bash
PARENT_DASHBOARD_REQUIRE_PASSWORD=False
```

With authentication disabled:
- No password required for parent dashboard
- Login endpoint still works but accepts any password
- Tokens still generated but not validated
- All endpoints accessible without Authorization header

## Troubleshooting

### "Authentication not properly configured"

**Problem:** Missing `PARENT_DASHBOARD_PASSWORD` or `JWT_SECRET_KEY`

**Solution:**
1. Run password manager utility
2. Generate password (option 1) and JWT secret (option 3)
3. Add both to `.env` file
4. Restart backend

### "Invalid or expired token"

**Problem:** Token has expired or is invalid

**Solution:**
1. Login again to get new token
2. Check token expiration time (default 8 hours)
3. Verify system clock is accurate

### "Invalid password"

**Problem:** Password doesn't match stored hash

**Solution:**
1. Verify you're using correct password
2. Check `PARENT_DASHBOARD_PASSWORD` in `.env` is correct hash
3. Regenerate password if needed

### Token not being sent

**Problem:** Requests fail with 401 even after login

**Solution:**
1. Verify token is being stored after login
2. Check Authorization header format: `Bearer <token>`
3. Ensure no extra spaces or characters in header

## Advanced Configuration

### Custom Token Expiration

Adjust token lifetime in `.env`:

```bash
# 1 hour
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# 24 hours
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 7 days
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

### Multiple Users (Future Enhancement)

The current system supports a single parent password. For multi-user support:

1. Create a users table with hashed passwords
2. Modify `auth_service.authenticate()` to query users table
3. Include user ID in JWT payload
4. Validate user ID on protected endpoints

### Custom JWT Claims

Add custom data to tokens:

```python
from services.auth_service import auth_service

token = auth_service.create_access_token(
    data={
        "sub": "parent",
        "user_id": 123,
        "permissions": ["read", "write"]
    }
)
```

Access claims in endpoints:

```python
@router.get("/example")
async def example(current_user: dict = RequireAuth):
    user_id = current_user.get("user_id")
    permissions = current_user.get("permissions", [])
    # Use claims...
```

## Integration with Frontend Frameworks

### React Example

```javascript
// AuthContext.js
import React, { createContext, useState, useContext } from 'react';

const AuthContext = createContext();

export function AuthProvider({ children }) {
    const [token, setToken] = useState(localStorage.getItem('auth_token'));

    const login = async (password) => {
        const response = await fetch('/api/parent/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });

        if (response.ok) {
            const { access_token } = await response.json();
            setToken(access_token);
            localStorage.setItem('auth_token', access_token);
            return true;
        }
        return false;
    };

    const logout = () => {
        setToken(null);
        localStorage.removeItem('auth_token');
    };

    const fetchWithAuth = async (url, options = {}) => {
        return fetch(url, {
            ...options,
            headers: {
                ...options.headers,
                'Authorization': `Bearer ${token}`
            }
        });
    };

    return (
        <AuthContext.Provider value={{ token, login, logout, fetchWithAuth }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);
```

**Usage:**
```javascript
import { useAuth } from './AuthContext';

function ParentDashboard() {
    const { fetchWithAuth } = useAuth();

    useEffect(() => {
        fetchWithAuth('/api/parent/dashboard/overview?user_id=1')
            .then(r => r.json())
            .then(data => console.log(data));
    }, []);

    return <div>Dashboard Content</div>;
}
```

## Summary

1. **Install** authentication dependencies
2. **Generate** password and JWT secret with password manager
3. **Configure** `.env` with hashed password and secret
4. **Login** to get JWT token
5. **Include** token in Authorization header for requests
6. **Verify** token periodically
7. **Logout** by discarding token

For questions or issues, check the troubleshooting section or server logs at `backend/logs/chatbot.log`.
