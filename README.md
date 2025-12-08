[![ru_readme](https://img.shields.io/badge/Readme-на_Русском-darkblue)](https://github.com/Tarasyonok/pet-project-forum/blob/main/README.ru.md)

# 🌙 Night Coder

> **Where Developers Code Together, Grow Together**  
> *Because code doesn't sleep, and neither do we* 🚀

![CI/CD](https://github.com/Tarasyonok/pet-project-forum/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![Django](https://img.shields.io/badge/Django-5.2-darkgreen?logo=django)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-blue?logo=postgresql)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.2-purple?logo=bootstrap)
![Ruff](https://img.shields.io/badge/Ruff-14-lightgreen?logo=ruff)
![Gunicorn](https://img.shields.io/badge/Gunicorn-23.0-green?logo=gunicorn)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?logo=docker)
![Railway](https://img.shields.io/badge/Railway-Hosting-white?logo=railway)
![License](https://img.shields.io/badge/License-MIT-yellow?logo=readme)

## 🎯 What is Night Coder?

**Night Coder** is a full-stack developer community platform built for those magical hours when creativity flows best.
It's where students, and passionate developers come together to ask questions, share knowledge, and grow their skills.

### ✨ Why Night Coder?

- 🕒 **Community** - Someone is always awake somewhere in the world
- 🏆 **Gamified Learning** - Earn reputation and climb leaderboards
- 🌐 **Bilingual** - English and Russian support for global reach
- 🎨 **Beautiful UI** - Dark theme optimized for night coding sessions
- 🤝 **Real Connections** - Build your developer reputation and portfolio

## 🚀 Night Coder Live

### 👉 **[Try Night Coder](https://pet-project-forum-production.up.railway.app/en/)** 👈

**Demo Credentials (if you don't want to create an account):**

- Nickname: `DemoUser`
- Email: `demo@nightcoder.com`
- Password: `DemoPass123`

## 📸 Screenshots

<details>
    <summary>🏠 Homepage</summary><br>
    <img src="/readme_screenshots/home_en.png" alt="Homepage" width="100%">
</details>
<details>
    <summary>👤 User Profile</summary>
    <br> <img src="/readme_screenshots/profile_en.png" alt="User Profile" width="100%">
</details>
<details>
    <summary>💬 Forum</summary><br>
    <img src="/readme_screenshots/forum_en.png" alt="Forum" width="100%">
</details>
<details>
    <summary>📚 Reviews</summary><br>
    <img src="/readme_screenshots/reviews_en.png" alt="Reviews" width="100%">
</details>
<details>
    <summary>🏆 Leaderboards</summary><br>
    <img src="/readme_screenshots/leaderboards_en.png" alt="Leaderboard" width="100%">
</details>

## 🛠️ Tech Stack

### **Backend**

- **Python 3.13** - Core programming language
- **Django 5.2** - Python Web framework
- **PostgreSQL 17** - Production database

### **Frontend**

- **Bootstrap 5** - Responsive CSS framework
- **JavaScript** - Interactive features
- **HTML5 & CSS3** - Modern web standards

### **DevOps & Tools**

- **Poetry** - Dependency management and packaging
- **Ruff** - Ultra-fast Python linter and formatter
- **Tests** - Unit & Integration tests
- **Git** - Version control with clean commit history
- **CI/CD** - Automated linting and testing
- **Gunicorn** - WSGI HTTP Server for production
- **Docker** - Containerization
- **Railway** - Deployment platform

## 🎨 Key Features

### 💬 **Q&A Forum**

- Ask programming questions and get answers
- Vote system with reputation rewards
- Mark answers as accepted
- Full-text search across questions and answers

### ⭐ **Course Reviews**

- Share experiences with programming courses
- 5-star rating system with detailed reviews
- Vote on helpful reviews
- Search by course name or technology

### 🏆 **Gamification System**

- **Reputation Points** - Earn through helpful contributions
- **Leaderboards** - Compete with other developers
- **Monthly Top Contributors** - Recognition for active members
- **Footer statistics** - Context processor for community stats on every page

### 👤 **User Profiles**

- Avatar upload and personal bios
- Activity history (questions, answers, reviews)
- Reputation breakdown and statistics
- Сontribution metrics

### 🌐 **Internationalization**

- Full English/Russian language support
- Language switcher
- SEO-friendly URL structure

### 🎯 **UX/UI**

- Dark theme optimized for coding
- Mobile-responsive design
- Accessible and keyboard-navigation friendly

## 📁 Project Structure

```
night-coder/
├── 🔧 core/                # Shared utilities & mixins
├── 💬 forum/               # Q&A functionality
├── 🏠 home/                # Homepage app
├── 🏆 leaderboards/        # Gamification system
├── 🌐 locale/              # Translation files
├── ⭐ reviews/             # Course reviews
├── 🗿 static/              # CSS, JS, images
├── 💄 templates/           # Django templates
├── 👤 users/               # Authentication & profiles
└── 👍 votes/               # Content votes
```

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Tarasyonok/pet-project-forum
   cd pet-project-forum
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your hosts and secret key
   ```

### Option 1: Docker (Recommended)

1. **Run with Docker**
   ```bash
   docker-compose up --build
   ```

### Option 2: Traditional Development

1. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install poetry
   poetry install
   ```

3. **Run migrations**
   ```bash
   python manage.py migrate
   ```

4. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run development server**
   ```bash
   python manage.py runserver
   ```

**Visit [localhost:8000](http://localhost:8000) and create your first question! 🌙**

## 🧪 Testing

```bash
python manage.py test
```

## 🔧 Code Quality

```bash
# Lint and format code
ruff check .          # Linting
ruff format .         # Formatting
```

## 🌐 Deployment

Night Coder is deployed on **Railway** with automatic CI/CD:

1. **Push to main branch** → Automatic deployment
2. **CI/CD** → Build after linting and testing pass
3. **Environment** → Production configuration

## 🤝 Contributing

We love contributions! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### If you have any feedback/suggestions for improvements, feel free to open an Issue

### Development Guidelines

- Follow PEP 8 style guide (use ruff)
- Write tests for new features
- Update documentation
- Use meaningful commit messages with emojis

## 🏆 Achievements

This project demonstrates mastery in:

- ✅ **Full-Stack Development** - End-to-end web application
- ✅ **Database Design** - Complex relationships and optimization
- ✅ **User Experience** - Intuitive and engaging interface
- ✅ **DevOps** - CI/CD, and cloud deployment
- ✅ **Containerization** - Docker and Docker Compose
- ✅ **Production Deployment** - PostgreSQL, Gunicorn, and environment management
- ✅ **Internationalization** - Multi-language support
- ✅ **Testing & Quality** - Comprehensive test coverage
- ✅ **Performance** - Fast loading and efficient queries

## 👨‍💻 About the Developer

**Kir Tarasov**  
*Full-Stack Developer*

- ✈️ **Telegram**: [@bravekirty](https://t.me/bravekirty)
- 🐙 **GitHub**: [@Tarasyonok](https://github.com/Tarasyonok)
- 📧 **Email**: bravekirty@gmail.com

[//]: # (- 🌳 **Linktree**: [@bravekirty]&#40;https://linktr.ee/bravekirty&#41;)

[//]: # (- 💼 **LinkedIn**: [Your LinkedIn]&#40;https://linkedin.com/in/your-profile&#41;)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

### **Ready to join our night coding community?** 🌙

[![Try Night Coder](https://img.shields.io/badge/Try_Night_Coder-Live-orange?style=for-the-badge)](https://pet-project-forum-production.up.railway.app/en/)

*⭐ Don't forget to star this repo if you found it interesting/helpful!*

</div>
