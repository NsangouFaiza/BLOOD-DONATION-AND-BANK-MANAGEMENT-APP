# FaiDrop - Blood Bank Management System

A comprehensive Django-based blood donation and bank management system designed for hospitals in Cameroon. This system facilitates blood donation management, patient-donor matching, and hospital blood bank operations.

## Features

### Core Functionalities
- **User Management**: Multi-role user system (Donors, Patients, Staff, Lab Technicians, Administrators)
- **Blood Donation**: Appointment scheduling, donor management, and blood collection tracking
- **Blood Testing**: Pre-donation testing and quality control management
- **Inventory Management**: Blood unit tracking, stock management, and expiration monitoring
- **Patient Services**: Blood requests, donor matching, and emergency coordination
- **Hospital Integration**: Multi-hospital support with individual blood bank management

### Security Features
- **OTP Verification**: SMS-based verification for account creation
- **National ID Verification**: Required ID card upload and verification
- **Role-Based Access Control**: Secure access based on user roles
- **Data Encryption**: Secure storage of sensitive information

### User Roles

#### Donors
- Register and complete profile
- Schedule donation appointments
- View donation history
- Receive notifications and updates

#### Patients
- Request blood from hospitals
- Search for direct donor matches
- Track request status
- Manage blood requirements

#### Hospital Staff
- Manage appointments
- Coordinate with donors
- Monitor blood inventory
- Handle patient requests

#### Lab Technicians
- Perform blood testing
- Update donor profiles
- Manage blood quality control
- Record test results

#### Administrators
- System oversight and management
- User verification and approval
- System monitoring and reporting
- Policy and configuration management

## Technology Stack

- **Backend**: Django 4.2.17 (Python)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: Django Templates + Bootstrap 5
- **Authentication**: Custom User Model + Django Auth
- **File Handling**: Pillow for image processing
- **Styling**: Bootstrap 5 + Custom CSS

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bloodbank
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy .env.example to .env and configure
   cp .env.example .env
   ```

5. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main site: http://localhost:8000/
   - Admin panel: http://localhost:8000/admin/

## Project Structure

```
bloodbank/
├── bloodbank/          # Main project settings
│   ├── settings.py     # Django configuration
│   ├── urls.py         # Main URL routing
│   └── wsgi.py         # WSGI configuration
├── core/               # Main application
│   ├── models.py       # Database models
│   ├── views.py        # View logic
│   ├── forms.py        # Form definitions
│   ├── admin.py        # Admin interface
│   └── urls.py         # App URL routing
├── templates/          # HTML templates
│   ├── base.html       # Base template
│   └── core/           # App-specific templates
├── static/             # Static files
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript files
│   └── images/         # Image assets
├── media/              # User-uploaded files
├── requirements.txt    # Python dependencies
└── README.md          # Project documentation
```

## Configuration

### Environment Variables
Create a `.env` file in the project root with the following variables:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
MEDIA_URL=/media/
STATIC_URL=/static/
```

### Database Configuration
The system supports multiple database backends:

- **SQLite** (default for development)
- **PostgreSQL** (recommended for production)
- **MySQL** (supported)

### Email Configuration
Configure email settings for OTP verification:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

## Usage

### For Donors
1. Register an account with valid phone number and national ID
2. Complete OTP verification
3. Fill out donor profile
4. Schedule donation appointments
5. Receive confirmation and reminders

### For Patients
1. Register as a patient
2. Submit blood requests (hospital or direct donor)
3. Track request status
4. Coordinate with matched donors

### For Hospital Staff
1. Access staff dashboard
2. Manage donor appointments
3. Monitor blood inventory
4. Process patient requests

### For Lab Technicians
1. Access lab dashboard
2. Perform blood testing
3. Update donor profiles
4. Manage quality control

### For Administrators
1. Access admin dashboard
2. Verify user accounts
3. Monitor system performance
4. Manage system configuration

## API Endpoints

The system provides RESTful API endpoints for integration:

- `/api/users/` - User management
- `/api/donors/` - Donor operations
- `/api/patients/` - Patient operations
- `/api/appointments/` - Appointment management
- `/api/blood-requests/` - Blood request handling
- `/api/inventory/` - Blood inventory management

## Security Considerations

- **Data Encryption**: Sensitive data is encrypted at rest
- **Input Validation**: Comprehensive form validation and sanitization
- **CSRF Protection**: Built-in Django CSRF protection
- **SQL Injection Prevention**: Django ORM protection
- **File Upload Security**: Secure file handling and validation
- **Session Management**: Secure session handling

## Deployment

### Production Checklist
- [ ] Set `DEBUG=False` in production
- [ ] Configure production database (PostgreSQL recommended)
- [ ] Set up static file serving (nginx/Apache)
- [ ] Configure media file storage
- [ ] Set up SSL/TLS certificates
- [ ] Configure backup systems
- [ ] Set up monitoring and logging
- [ ] Configure email services

### Docker Deployment
```bash
# Build the image
docker build -t bloodbank .

# Run the container
docker run -p 8000:8000 bloodbank
```

### Cloud Deployment
The system is compatible with:
- **AWS**: EC2, RDS, S3, CloudFront
- **Azure**: App Service, SQL Database, Blob Storage
- **Google Cloud**: App Engine, Cloud SQL, Cloud Storage
- **Heroku**: Platform as a Service

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## Acknowledgments

- Django community for the excellent framework
- Bootstrap team for the UI components
- Font Awesome for the icons
- All contributors and testers

## Changelog

### Version 1.0.0
- Initial release
- Core blood bank functionality
- User management system
- Multi-role support
- Security features implementation

---

**Note**: FaiDrop is designed specifically for the Cameroonian healthcare context and includes features to address local challenges such as internet connectivity, language diversity, and staff training requirements.
