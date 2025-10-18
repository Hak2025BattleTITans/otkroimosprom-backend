# API Documentation v1

## Authentication

### POST `/api/v1/auth/register`

Регистрация нового пользователя в системе.

**Request Body (JSON)**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `username` | string | Да | Имя пользователя (3-50 символов) |
| `password` | string | Да | Пароль (минимум 6 символов) |

**Response 201**

```json
{
  "id": 1,
  "username": "newuser",
  "created_at": "2025-01-18T14:30:00Z",
  "updated_at": "2025-01-18T14:30:00Z"
}
```

**Response 400**

```json
{
  "detail": "Username already registered"
}
```

---

### POST `/api/v1/auth/login`

Авторизация пользователя через form-data (стандартный OAuth2).

**Form Data (x-www-form-urlencoded)**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `username` | string | Да | Имя пользователя |
| `password` | string | Да | Пароль пользователя |

**Response 200**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Response 401**

```json
{
  "detail": "Incorrect username or password"
}
```

---

### POST `/api/v1/auth/login-json`

Авторизация пользователя через JSON (альтернативный способ).

**Request Body (JSON)**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `username` | string | Да | Имя пользователя |
| `password` | string | Да | Пароль пользователя |

**Response 200**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Response 401**

```json
{
  "detail": "Incorrect username or password"
}
```

---

### GET `/api/v1/auth/me`

Получить информацию о текущем авторизованном пользователе.

**Headers**
| Заголовок | Тип | Обязательно | Описание |
|--------------------|--------|--------------|----------|
| `Authorization` | string | Да | `Bearer <JWT>` полученный из login эндпоинтов |

**Response 200**

```json
{
  "id": 1,
  "username": "user123",
  "created_at": "2025-01-18T14:30:00Z",
  "updated_at": "2025-01-18T14:30:00Z"
}
```

**Response 401**

```json
{
  "detail": "Could not validate credentials"
}
```

---

## Files

### POST `/api/v1/files/upload`

Загрузка CSV файла с данными предприятий и их обработка.

**Headers**
| Заголовок | Тип | Обязательно | Описание |
|--------------------|--------|--------------|----------|
| `Authorization` | string | Да | `Bearer <JWT>` токен авторизации |

**Form Data (multipart/form-data)**
| Поле | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `file` | file | Да | CSV файл с данными предприятий |
| `as_name` | string | Нет | Альтернативное имя для файла |

**Response 200**

```json
{
  "file_name": "companies.csv",
  "stored_name": "abc123_companies.csv",
  "size_bytes": 1024000,
  "companies_processed": 150,
  "companies_saved": [
    {
      "id": 1,
      "name": "ООО Компания 1",
      "inn": 1234567890
    },
    {
      "id": 2,
      "name": "АО Компания 2",
      "inn": 9876543210
    }
  ]
}
```

**Response 400**

```json
{
  "detail": "Only CSV files are allowed"
}
```

**Response 413**

```json
{
  "detail": "File too large (limit 50 MB)"
}
```

---

### GET `/api/v1/files/companies`

Получить список компаний, загруженных текущим пользователем.

**Headers**
| Заголовок | Тип | Обязательно | Описание |
|--------------------|--------|--------------|----------|
| `Authorization` | string | Да | `Bearer <JWT>` токен авторизации |

**Query Parameters**
| Параметр | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `limit` | integer | Нет | Количество записей (по умолчанию: 50) |
| `offset` | integer | Нет | Смещение (по умолчанию: 0) |

**Response 200**

```json
{
  "companies": [
    {
      "id": 1,
      "name": "ООО Компания 1",
      "inn": 1234567890,
      "main_industry": "IT",
      "company_size_final": "Среднее",
      "support_measures": true,
      "special_status": "Есть"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

---

### GET `/api/v1/files/companies/{company_id}`

Получить детальную информацию о конкретной компании.

**Headers**
| Заголовок | Тип | Обязательно | Описание |
|--------------------|--------|--------------|----------|
| `Authorization` | string | Да | `Bearer <JWT>` токен авторизации |

**Path Parameters**
| Параметр | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `company_id` | integer | Да | ID компании |

**Response 200**

```json
{
  "id": 1,
  "inn": 1234567890,
  "name": "ООО Компания 1",
  "full_name": "Общество с ограниченной ответственностью Компания 1",
  "spark_status": "Действующая",
  "main_industry": "IT",
  "company_size_final": "Среднее",
  "organization_type": "ООО",
  "support_measures": true,
  "special_status": "Есть",
  "confirmation_status": "Не подтверждён",
  "json_data": {
    "ИНН": "1234567890",
    "Наименование организации": "ООО Компания 1",
    "Основная отрасль": "IT",
    "Выручка предприятия, тыс. руб. 2023": 5000000
  }
}
```

**Response 404**

```json
{
  "detail": "Company not found"
}
```

---

### GET `/api/v1/files/companies/{company_id}/json`

Получить полные JSON данные компании из исходного CSV файла.

**Headers**
| Заголовок | Тип | Обязательно | Описание |
|--------------------|--------|--------------|----------|
| `Authorization` | string | Да | `Bearer <JWT>` токен авторизации |

**Path Parameters**
| Параметр | Тип | Обязательно | Описание |
|------------|-------|--------------|----------|
| `company_id` | integer | Да | ID компании |

**Response 200**

```json
{
  "company_id": 1,
  "json_data": {
    "ИНН": "1234567890",
    "Наименование организации": "ООО Компания 1",
    "Полное наименование организации": "Общество с ограниченной ответственностью Компания 1",
    "Статус СПАРК": "Действующая",
    "Основная отрасль": "IT",
    "Размер предприятия (итог)": "Среднее",
    "Выручка предприятия, тыс. руб. 2023": 5000000,
    "Чистая прибыль (убыток),тыс. руб. 2023": 500000,
    "Среднесписочная численность персонала (всего по компании), чел 2023": 100
  }
}
```

**Response 404**

```json
{
  "detail": "Company not found"
}
```

---

## Error Responses

### 401 Unauthorized

```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden

```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found

```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error"
}
```
