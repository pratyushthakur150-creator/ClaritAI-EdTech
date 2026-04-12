# Ravian Backend + Frontend – Auth Flow Setup

Use this guide to get the backend and frontend running with working registration and login.

---

## 1. Database setup

### 1.1 Confirm PostgreSQL and database

- PostgreSQL 16 is running (e.g. via pgAdmin).
- Database `ravian_dev` exists.
- In backend `.env`, DB settings match your DB:

  - Path: `C:\Users\praty\OneDrive\Desktop\Edtech admission Final\ravian-backend\ravian-backend\ravian-backend\.env`
  - Example:
    ```env
    DB_HOST=localhost
    DB_PORT=5433
    DB_USER=postgres
    DB_PASSWORD=ClaritAI
    DB_NAME=ravian_dev
    ```

### 1.2 Create tables (migrations)

Open **PowerShell** and run:

```powershell
cd "C:\Users\praty\OneDrive\Desktop\Edtech admission Final\ravian-backend\ravian-backend\ravian-backend"
.\venv\Scripts\Activate.ps1
python -m alembic upgrade head
```

- If you see execution policy errors:  
  `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- To verify tables in pgAdmin: connect to `ravian_dev` → Schemas → public → Tables. You should see `tenants`, `users`, `leads`, etc.

### 1.3 Optional: create tables without Alembic

If you prefer to create tables from the app (no migrations):

```powershell
cd "C:\Users\praty\OneDrive\Desktop\Edtech admission Final\ravian-backend\ravian-backend\ravian-backend"
.\venv\Scripts\python.exe -c "from app.core.database import create_tables; create_tables(); print('Tables created')"
```

---

## 2. Backend

### 2.1 Start backend

```powershell
cd "C:\Users\praty\OneDrive\Desktop\Edtech admission Final\ravian-backend\ravian-backend\ravian-backend"
.\venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- API: http://127.0.0.1:8000  
- Swagger: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/health  

### 2.2 Test registration in Swagger

1. Open http://127.0.0.1:8000/docs  
2. Find **POST /api/v1/auth/register**  
3. Try it out with:

```json
{
  "email": "admin@school.com",
  "password": "Admin@123",
  "first_name": "Admin",
  "last_name": "User",
  "tenant_name": "TestSchool",
  "role": "ADMIN"
}
```

4. Expect **201** and a user object. If you get **500**, check the backend terminal for the traceback (e.g. missing table, wrong DB URL).

### 2.3 Test login in Swagger

1. **POST /api/v1/auth/login** with:

```json
{
  "email": "admin@school.com",
  "password": "Admin@123"
}
```

2. Expect **200** with `access_token`, `refresh_token`, and `user`.

---

## 3. Frontend

### 3.1 API URL

- Frontend path:  
  `C:\Users\praty\OneDrive\Desktop\Edtech admission Final\ravian-backend\ravian-backend\ravian-frontend`
- Create or edit `.env.local` in that folder:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

(Already set to this in your project.)

### 3.2 Start frontend

```powershell
cd "C:\Users\praty\OneDrive\Desktop\Edtech admission Final\ravian-backend\ravian-backend\ravian-frontend"
npm install
npm run dev
```

- App: http://localhost:3000  
- Login: http://localhost:3000/login  
- Register: http://localhost:3000/register  

### 3.3 Test flow in the UI

1. **Register**  
   - Go to http://localhost:3000/register  
   - Fill: First name, Last name, Email, Password (min 8), Organization (e.g. TestSchool), Role (e.g. Admin)  
   - Submit → should redirect to login.

2. **Login**  
   - Go to http://localhost:3000/login  
   - Use the same email and password  
   - Submit → should redirect to dashboard; JWT is stored and used for API calls.

---

## 4. Troubleshooting

### Registration returns 500

- Check backend terminal for the full error.
- Confirm DB: `.env` has correct `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`.
- Confirm tables exist (see 1.2–1.3).

### Frontend can’t reach backend (CORS / network)

- Backend CORS is set to allow all origins (`["*"]`). No change needed for localhost.
- Ensure backend is running on http://127.0.0.1:8000 and `.env.local` has `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000`.
- In browser DevTools → Network, check the failing request (URL, status, response).

### Login shows “Incorrect email or password”

- Use the same email/password you used in Swagger or on the register page.
- Ensure the user exists (e.g. register again or check `users` table in pgAdmin).

### JWT / 401 after login

- Frontend stores `access_token` in `localStorage` and sends it as `Authorization: Bearer <token>` (see `lib/api.ts`).
- If you still get 401, check that the backend `/api/v1/auth/me` (or the endpoint you call) is in the public paths or that the token is valid and not expired.

---

## 5. Quick reference

| Item        | Path / URL |
|------------|------------|
| Backend dir | `...\ravian-backend\ravian-backend\ravian-backend` |
| Backend .env | Same folder as above |
| Frontend dir | `...\ravian-backend\ravian-backend\ravian-frontend` |
| Frontend .env | `.env.local` in frontend dir |
| API base    | http://127.0.0.1:8000 |
| Swagger     | http://127.0.0.1:8000/docs |
| Login page | http://localhost:3000/login |
| Register   | http://localhost:3000/register |

---

**Desired end state:** Backend and frontend running; register from `/register`; login from `/login`; JWT used for authenticated requests.
