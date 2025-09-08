# Overview

ChatBot Factory is a multi-platform AI chatbot creation and management platform that enables users to build intelligent chatbots for Telegram, Instagram, and WhatsApp using Google Gemini AI. The platform provides a web-based interface for creating, configuring, and managing chatbots without requiring coding knowledge.

The application follows a modular architecture with separate services for different messaging platforms, AI integration, and user management. It supports multiple languages (English, Uzbek, Russian) and includes subscription-based access control with different tiers of service.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: Flask with Jinja2 templating
- **UI Framework**: Bootstrap 5 with custom CSS styling
- **Client-side**: Vanilla JavaScript with progressive enhancement
- **Internationalization**: Flask-Babel for multi-language support (en, uz, ru)
- **Responsive Design**: Mobile-first approach with Bootstrap grid system

## Backend Architecture
- **Web Framework**: Flask with application factory pattern
- **Database ORM**: SQLAlchemy with Flask-SQLAlchemy integration
- **Authentication**: Flask-Login for session management
- **Database Migrations**: Flask-Migrate for schema versioning
- **Architecture Pattern**: Modular service-oriented design with clear separation of concerns

## Data Storage
- **Primary Database**: SQLite for development, configurable for PostgreSQL in production
- **ORM Models**: User, Bot, Subscription, Conversation, Message, BotAnalytics with enum-based status tracking
- **Session Management**: Flask's built-in session handling with secure secret keys
- **Migration System**: Alembic-based migrations through Flask-Migrate

## Authentication & Authorization
- **User Authentication**: Username/password-based login with password hashing via Werkzeug
- **Session Management**: Flask-Login for user session persistence
- **Role-based Access**: Admin privileges with is_admin flag
- **Subscription Controls**: Tier-based feature limiting (FREE, STARTER, BASIC, PREMIUM)

## Bot Management System
- **Multi-platform Support**: Telegram (implemented), Instagram (placeholder), WhatsApp (placeholder)
- **Bot Lifecycle**: Create, configure, start/stop, delete operations
- **Status Tracking**: ACTIVE, INACTIVE, PENDING states with enum-based validation
- **Real-time Operation**: Threading-based bot execution for Telegram bots

## AI Integration
- **Primary AI Service**: Google Gemini API integration
- **Conversation Context**: Historical message tracking for contextual responses
- **Personality System**: Configurable bot personalities through system prompts
- **Response Analytics**: Token usage and response time tracking

# External Dependencies

## Third-party Services
- **Google Gemini API**: Primary AI language model for chatbot responses
- **Telegram Bot API**: Real-time bot integration with python-telegram-bot library
- **Instagram Business API**: Placeholder for future Instagram bot functionality
- **WhatsApp Business Platform**: Placeholder for future WhatsApp bot integration

## Key Python Packages
- **Flask**: Web framework with extensions (SQLAlchemy, Login, Migrate, Babel)
- **python-telegram-bot**: Telegram Bot API wrapper for bot operations
- **google-genai**: Google Gemini AI API client
- **Werkzeug**: Security utilities for password hashing and proxy handling
- **Gunicorn**: WSGI HTTP server for production deployment

## Database Systems
- **Development**: SQLite with file-based storage
- **Production Ready**: PostgreSQL support through configurable DATABASE_URL
- **Connection Management**: Pool recycling and pre-ping for reliability

## Frontend Libraries
- **Bootstrap 5**: UI component framework
- **Font Awesome**: Icon library
- **Custom CSS**: Theme system with CSS custom properties

## Environment Configuration
- **Secret Management**: Environment variable-based configuration
- **API Keys**: Secure storage for GEMINI_API_KEY, platform tokens
- **Session Security**: Configurable SESSION_SECRET for session encryption
- **Database URLs**: Flexible database connection string configuration