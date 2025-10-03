# API Docs

## Auth

### POST `/api/v1/auth/login`

Авторизация пользователя и получение JWT токена. Единственный валидный логин — `admin`. Пароль берётся из переменной окружения `.env` → `ADMIN_PASSWORD`.

**Form data (x-www-form-urlencoded)**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `username` | string | Да | Имя пользователя. Для данной версии — всегда `admin`. |
| `password` | string | Да | Пароль администратора (`ADMIN_PASSWORD` из `.env`). |

**Response 200**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Response 401**

```json
{
  "detail": "Incorrect username or password"
}
```

---

### GET `/api/auth/me`

Получить профиль текущего пользователя по Bearer-токену.

**Headers**
| Заголовок | Тип | Обязательно | Описание |
|--------------------|--------|--------------|----------|
| `Authorization` | string | Да | `Bearer <JWT>` полученный из [`/api/auth/login`](#post-apiauthlogin). |

**Response 200**

```json
{
  "id": 1,
  "username": "admin",
  "full_name": null,
  "role": "admin",
  "created_at": "2025-09-27T12:00:00Z"
}
```

**Response 401**

```json
{
  "detail": "Could not validate credentials"
}
```
