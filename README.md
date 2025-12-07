# InsightBlog

A modern, API-first blogging platform built with FastAPI and featuring social interactions, JWT authentication, and a clean separation between backend and frontend.

## 🚀 Features

### Core Features
- 📝 **Blog Posts** - Create, read, and delete blog posts with rich content
- 🔐 **JWT Authentication** - Secure token-based authentication
- 👤 **User Profiles** - Customizable profiles with avatar upload
- 📱 **Responsive Design** - Modern UI with Tailwind CSS

### Social Features
- ❤️ **Likes** - Like and unlike posts
- 💬 **Comments** - Nested comment system with replies
- 🔄 **Shares** - Share posts with others
- 🔔 **Notifications** - Real-time notifications for admins

### API-First Architecture
- 🎯 **RESTful APIs** - All endpoints return JSON
- 📊 **Pagination** - Efficient data loading with pagination
- 🔒 **Secure** - JWT tokens, password hashing, input validation
- 📖 **Well-documented** - Complete API documentation included

## 📸 Gallery

<div align="center">
  <img src="static/git/images/3_dashboard.png" alt="Dashboard" width="800"/>
  <p><em>Modern Dashboard with Grid Layout</em></p>
</div>

<div align="center">
  <img src="static/git/images/5_post_view.png" alt="Post View" width="800"/>
  <p><em>Immersive Post Reading Experience</em></p>
</div>

<div align="center">
   <table border="0">
      <tr>
         <td width="50%">
            <p align="center"><b>Login with Glassmorphism</b></p>
            <img src="static/git/images/1_login_page.png" width="100%"/>
         </td>
         <td width="50%">
            <p align="center"><b>Registration Flow</b></p>
            <img src="static/git/images/2_register_page.png" width="100%"/>
         </td>
      </tr>
      <tr>
         <td>
            <p align="center"><b>Public Profiles</b></p>
            <img src="static/git/images/7_public_profile.png" width="100%"/>
         </td>
         <td>
            <p align="center"><b>User Settings</b></p>
            <img src="static/git/images/6_profile_settings.png" width="100%"/>
         </td>
      </tr>
      <tr>
         <td>
            <p align="center"><b>Notifications Center</b></p>
            <img src="static/git/images/8_notifications.png" width="100%"/>
         </td>
         <td>
            <p align="center"><b>Create Post Editor</b></p>
            <img src="static/git/images/4_create_post_page.png" width="100%"/>
         </td>
      </tr>
      <tr>
         <td>
            <p align="center"><b>Forgot Password</b></p>
            <img src="static/git/images/9_forgot_password.png" width="100%"/>
         </td>
         <td>
            <p align="center"><b>Reset Password</b></p>
            <img src="static/git/images/10_reset_password.png" width="100%"/>
         </td>
      </tr>
   </table>
</div>

## 🛠️ Tech Stack

**Backend:**
- FastAPI (Python web framework)
- PostgreSQL (Database)
- SQLAlchemy (ORM)
- JWT (Authentication)
- Pydantic (Data validation)

**Frontend:**
- Jinja2 Templates
- Tailwind CSS
- Vanilla JavaScript
- Fetch API for AJAX calls

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL
- UV (Python package manager)

## 🔧 Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd insightblog
```

2. **Install dependencies**
```bash
uv sync
```

3. **Set up environment variables**

Create a `.env` file in the root directory:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/insightblog
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

4. **Initialize the database**
```bash
uv run reset_schema.py
```

This will:
- Create all database tables
- Set up the schema
- Create a default admin user

**Default Admin Credentials:**
- Email: `admin@insightblog.com`
- Password: `admin123`

⚠️ **Important:** Change the admin password after first login!

## 🚀 Running the Application

```bash
uv run main.py
```

The application will be available at `http://localhost:8000`

## 📚 API Documentation

### Authentication Endpoints

**Register**
```http
POST /api/v1/users/register
Content-Type: application/json

{
  "email": "user@example.com",
  "full_name": "John Doe",
  "password": "securepassword"
}
```

**Login**
```http
POST /api/v1/users/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Posts Endpoints

**List Posts (Paginated)**
```http
GET /api/v1/posts/?skip=0&limit=20&published_only=true
Authorization: Bearer {token}
```

**Get Single Post**
```http
GET /api/v1/posts/{post_id}
Authorization: Bearer {token}
```

**Create Post**
```http
POST /api/v1/posts/
Authorization: Bearer {token}
Content-Type: multipart/form-data

title=My Post
summary=Post summary
category=Technology
tags=ai,ml
image=<file>
```

**Like Post**
```http
POST /api/v1/posts/{post_id}/like
Authorization: Bearer {token}
```

**Add Comment**
```http
POST /api/v1/posts/{post_id}/comments
Authorization: Bearer {token}
Content-Type: application/json

{
  "content": "Great post!",
  "parent_id": null
}
```

For complete API documentation, see [API Documentation](./brain/api_documentation.md)

## 📁 Project Structure

```
insightblog/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/      # API endpoints
│   │           ├── users.py    # User/auth endpoints
│   │           └── posts.py    # Post endpoints
│   ├── core/
│   │   ├── config.py          # Configuration
│   │   └── logging.py         # Logging setup
│   ├── db/
│   │   ├── session.py         # Database session
│   │   └── seed.py            # Database seeding
│   ├── models/
│   │   ├── user.py            # User model
│   │   └── blog.py            # Blog models
│   ├── schemas/
│   │   └── user.py            # Pydantic schemas
│   ├── services/
│   │   ├── auth.py            # Authentication logic
│   │   └── otp.py             # OTP generation
│   ├── web/
│   │   └── routes.py          # Web routes (templates only)
│   └── main.py                # Application entry point
├── templates/                  # Jinja2 templates
├── static/                     # Static files (CSS, JS, images)
├── .env                        # Environment variables
├── reset_schema.py            # Database reset script
└── README.md                  # This file
```

## 🎯 Usage

### Creating a Post

1. Login to your account
2. Click "Create Post"
3. Fill in the title, summary, category, and tags
4. Upload an optional featured image
5. Click "Create Post"

All posts are automatically published.

### Social Interactions

- **Like**: Click the heart icon on any post
- **Comment**: Write a comment at the bottom of a post
- **Reply**: Click "Reply" on any comment to add a nested reply
- **Share**: Click the share button to share a post

### Admin Features

Admins can:
- Delete any post
- Delete any comment
- View all notifications
- Moderate content

## 🔒 Security Features

- JWT token-based authentication
- Password hashing with bcrypt
- HTTP-only cookies for tokens
- Input validation with Pydantic
- SQL injection protection via ORM
- CORS configuration

## 🧪 Testing

The application includes:
- API endpoint testing
- Authentication flow testing
- Database operations testing

## 📝 License

This project is licensed under the MIT License.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For support, email admin@insightblog.com or open an issue in the repository.

---

**Built with ❤️ using FastAPI and modern web technologies**
