# microservice_test
Bu Microservice amalyot uchun, java va python bilan birgalikda

microservice_test/
├── auth-service/           # Python FastAPI (autentifikatsiya)
├── user-service/           # Java Spring Boot (foydalanuvchi ma'lumotlari)
├── post-service/           # Java Spring Boot (postlar)
├── admin-service/          # Python Django (administrator panel)
├── target-service/         # Python FastAPI (maqsadlar)
├── notification-service/   # Java Spring Boot (bildirishnomalar)
├── api-gateway/           # Spring Cloud Gateway (API shlyuzi)
├── service-registry/      # Eureka (xizmatlar ro'yxati)
├── docker-compose.yml     # Barcha servislarni ishga tushirish
└── README.md             # Loyiha haqida ma'lumot

---

Zo‘r! Siz va sherigingiz **har xil texnologiyalar (Java Spring Boot + Python FastAPI/Django)** bilan **birgalikda microservices arxitekturasi** qurayotgan ekansiz — bu haqiqiy real hayotdagi cross-stack muhit tajribasi bo‘ladi. Quyida loyiha **poliglot arxitektura** asosida professional tarzda qayta tuzilgan.

---

## 🔄 Yangilangan: DoPost loyihasi – **Cross-stack Microservices Architecture**

---

### 🧱 1. Asosiy Microservice-lar va kim nima yozadi:

| Service              | Texnologiya            | Mas’ul      | Tavsif                      |
| -------------------- | ---------------------- | ----------- | --------------------------- |
| **Auth Service**     | FastAPI (JWT)          | Sherigingiz | Login, signup, JWT, roles   |
| **User Service**     | Spring Boot            | Siz         | Profil CRUD, avatar, bio    |
| **Post Service**     | Spring Boot            | Siz         | Post CRUD, public/my feed   |
| **Admin Service**    | Django Admin Panel     | Sherigingiz | User & post management      |
| **Target Service**   | FastAPI                | Sherigingiz | Targetlar qo‘yish, kuzatish |
| **Notification**     | Spring Boot + RabbitMQ | Siz         | Email, xabarnomalar         |
| **API Gateway**      | Spring Cloud Gateway   | Siz         | Barcha client chaqiriqlari  |
| **Service Registry** | Eureka                 | Siz         | Service discovery           |


---

## ⚙️ Texnologiyalar muvofiqlashtirilgan to‘plami:

| Layer            | Java Stack (Siz)                  | Python Stack (Sherigingiz) |
| ---------------- | --------------------------------- | -------------------------- |
| Framework        | Spring Boot                       | FastAPI / Django           |
| Auth             | Spring Security (gatewayda check) | FastAPI + JWT              |
| DB               | PostgreSQL / MongoDB              | PostgreSQL                 |
| Messaging        | RabbitMQ                          | Pika (Python client)       |
| Caching          | Redis                             | Redis                      |
| File storage     | MinIO / AWS S3                    | MinIO / boto3              |
| Containerization | Docker, Docker Compose            | Docker                     |
| Docs             | Swagger (springdoc-openapi)       | Swagger / ReDoc            |

---

## 📡 3. Arxitektura – Microservices diagram (oddiy model)

```text
                      +---------------------+
                      |    API Gateway      |
                      +---------------------+
                               |
        ---------------------------------------------------
        |            |              |            |         |
     Auth         User           Post         Admin     Target
 (FastAPI)    (Spring Boot)  (Spring Boot)   (Django)  (FastAPI)

                 ↘       ↘           ↘         ↘
              Notification  (RabbitMQ listener)
               (Spring Boot)
```

---

## 📩 4. Servislararo muloqot

### 🔁 **Sync (HTTP, REST)**

* Frontend → Gateway → Microservices (Spring Cloud Gateway route)
* API Gateway tokenni tekshiradi (JWT)

### 🔀 **Async (RabbitMQ eventlar)**

* `UserRegistered` → Notification
* `PostCreated` → Admin Service yoki Notification
* `TargetAssigned` → Notification

> **Exchange**: topic
> **Event format**: JSON payload (`event_type`, `data`, `source_service`)

---

## 🧩 5. Service bo‘yicha muhim detallari

### Auth Service (FastAPI)

* `/auth/register`, `/auth/login`, `/auth/refresh`
* JWT tokenlar (access + refresh)
* Role-based: `ROLE_USER`, `ROLE_ADMIN`
* Token validation uchun gatewayda interceptor/`filter` yozing (Spring Boot)

### User Service (Spring Boot)

* `/users/me`, `/users/{id}`, `/users/me/avatar`
* PostgreSQL
* Tokenni gateway orqali validate qilinadi

### Post Service (Spring Boot)

* `/posts`, `/posts/{id}`, `/users/{id}/posts`, `/feed`
* MongoDB tavsiya etiladi
* Async event: `PostCreated`, `PostDeleted`

### Admin Service (Django)

* Django Admin Panel orqali web UI ham bo‘ladi
* Django Rest Framework bilan API ham qo‘shilishi mumkin
* `/admin/users`, `/admin/posts`, `/admin/stats`

### Target Service (FastAPI)

* `/targets`, `/targets/assign`, `/targets/my`
* Target progress hisoblash

### Notification Service (Spring Boot)

* Listener sifatida ishlaydi
* `emailService.send()`, RabbitMQ listener
* SMTP yoki mock xabar chiqarish

---

## 🛠 6. Docker Compose strukturasi

```
dopost/
├── auth-service/        (Python - FastAPI)
├── user-service/        (Java - Spring Boot)
├── post-service/        (Java - Spring Boot)
├── admin-service/       (Python - Django)
├── target-service/      (Python - FastAPI)
├── notification-service/(Java - Spring Boot)
├── api-gateway/         (Spring Cloud Gateway)
├── service-registry/    (Eureka)
├── config-server/       (Spring Cloud Config)
└── docker-compose.yml
```

---

## 📋 7. Ishlarni birga bo‘lishish taklifi (taqsimoti)

| Bo‘lim                | Siz (Java)            | Sherigingiz (Python)        |
| --------------------- | --------------------- | --------------------------- |
| User Service          | ✅                     | ❌                           |
| Post Service          | ✅                     | ❌                           |
| Notification Listener | ✅                     | ❌                           |
| Auth Service          | ❌                     | ✅ (FastAPI + JWT)           |
| Target Service        | ❌                     | ✅ (FastAPI)                 |
| Admin Panel           | ❌                     | ✅ (Django + DRF)            |
| Service Registry      | ✅                     | ❌                           |
| API Gateway           | ✅                     | ❌                           |
| Common Docker Compose | ✅ (siz tuzgan yaxshi) | 🔄 Alohida Python konteyner |

---

## 🔐 JWT tokenni Gateway orqali tekshirish (Java)

* Gateway’da Spring Security + Custom JWT filter ishlatish kerak
* Har bir requestda `Authorization: Bearer <token>` header bo‘ladi
* Agar token noto‘g‘ri yoki muddati o‘tgan bo‘lsa, `403` qaytariladi

---

Agar xohlasangiz, keyingi bosqichlarda siz uchun:

* `docker-compose.yml` fayl
* `spring-cloud-gateway` uchun JWT filter kodi
* Spring Boot service template (user/post)
* FastAPI auth service dizayni
* RabbitMQ listener misoli

tayyorlab beraman. Qaysidan boshlaymiz?
