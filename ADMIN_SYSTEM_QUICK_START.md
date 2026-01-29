# Admin System Quick Start Guide

## Accessing the Admin Dashboard

### URL
```
http://localhost:5000/admin-management/dashboard
```

### Requirements
- Must be logged in as a user with `role="admin"`
- Must have an Admin profile with `role="super_admin"`

## Creating Your First Super Admin

### Option 1: Using Python Script
```python
from core.app_factory import create_app
from core.extensions import db
from models.user import User
from models.admin import Admin
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # Create user
    user = User(
        username="super_admin",
        email="admin@koachsmart.com",
        password=generate_password_hash("YourSecurePassword123"),
        role="admin"
    )
    db.session.add(user)
    db.session.commit()
    
    # Create admin profile
    admin = Admin(
        user_id=user.id,
        role="super_admin"
    )
    admin.generate_api_credentials()
    db.session.add(admin)
    db.session.commit()
    
    print(f"Super Admin Created!")
    print(f"Email: {user.email}")
    print(f"API Key: {admin.api_key}")
    print(f"API Secret: {admin.api_secret}")
```

### Option 2: Using create_admin.py Script
```bash
py create_admin.py
```

## Admin Dashboard Features

### 1. Dashboard (`/admin-management/dashboard`)
- View total admins count
- See active admins
- Total verifications and approvals
- Recent activity feed
- Quick admin overview

### 2. Admin List (`/admin-management/admins`)
- View all admins
- Filter by status (active/inactive)
- Filter by city
- Quick actions (edit, view, delete)

### 3. Create Admin (`/admin-management/admin/create`)
- Add new regional admin
- Assign cities
- Set initial permissions
- Auto-generate API credentials

### 4. Edit Admin (`/admin-management/admin/<id>/edit`)
- Update city assignments
- Modify permissions
- View performance metrics
- See activity statistics

### 5. Admin Credentials (`/admin-management/admin/<id>/credentials`)
- View API key and secret
- Copy credentials to clipboard
- Regenerate credentials (with confirmation)
- Secure credential display

### 6. Activity Log (`/admin-management/admin/<id>/activity`)
- View all admin actions
- Paginated results (20 per page)
- Detailed change tracking
- Filter by action type

### 7. Performance Metrics (`/admin-management/admin/<id>/performance`)
- Total verifications
- Approval/rejection counts
- Approval rate percentage
- Recent activities
- Performance charts

### 8. Admin Reports (`/admin-management/reports/admins`)
- Overall platform statistics
- Individual admin performance
- Export to CSV
- Print reports

## Admin Roles & Permissions

### Super Admin
- Full platform access
- Manage all admins
- Access all cities
- All permissions enabled

**Permissions:**
- ✅ verify_coaches
- ✅ approve_documents
- ✅ manage_admins
- ✅ view_analytics
- ✅ handle_appeals
- ✅ send_notifications
- ✅ export_reports

### Regional Admin
- City-level access
- Verify coaches in assigned cities
- Limited admin functions

**Permissions:**
- ✅ verify_coaches
- ✅ approve_documents
- ❌ manage_admins
- ✅ view_analytics
- ✅ handle_appeals
- ✅ send_notifications
- ✅ export_reports

## Common Tasks

### Create a Regional Admin for Mumbai
```python
admin = Admin(
    user_id=user.id,
    role="regional_admin",
    assigned_cities=["Mumbai"]
)
admin.generate_api_credentials()
db.session.add(admin)
db.session.commit()
```

### Add More Cities to an Admin
```python
admin = Admin.query.get(admin_id)
admin.add_city("Pune")
admin.add_city("Nagpur")
db.session.commit()
```

### Check Admin Permissions
```python
admin = Admin.query.get(admin_id)

# Check specific permission
if admin.has_permission('verify_coaches'):
    print("Can verify coaches")

# Check city access
if admin.can_access_city('Mumbai'):
    print("Can access Mumbai")
```

### Log Admin Activity
```python
admin.log_activity(
    action="verify_document",
    entity_type="coach",
    entity_id=123,
    old_value={"status": "pending"},
    new_value={"status": "verified"},
    ip_address="192.168.1.1"
)
```

### Deactivate an Admin
```python
admin = Admin.query.get(admin_id)
admin.is_active = False
db.session.commit()
```

### Regenerate Admin Credentials
```python
admin = Admin.query.get(admin_id)
api_key, api_secret = admin.generate_api_credentials()
db.session.commit()
print(f"New API Key: {api_key}")
print(f"New API Secret: {api_secret}")
```

## API Endpoints Reference

### Dashboard & Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin-management/dashboard` | Super admin dashboard |
| GET | `/admin-management/admins` | List all admins |
| GET | `/admin-management/admin/create` | Create admin form |
| POST | `/admin-management/admin/create` | Create new admin |
| GET | `/admin-management/admin/<id>/edit` | Edit admin form |
| POST | `/admin-management/admin/<id>/edit` | Update admin |
| POST | `/admin-management/admin/<id>/toggle` | Toggle status |
| POST | `/admin-management/admin/<id>/delete` | Delete admin |

### Credentials & Activity
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin-management/admin/<id>/credentials` | View credentials |
| POST | `/admin-management/admin/<id>/credentials/regenerate` | Regenerate credentials |
| GET | `/admin-management/admin/<id>/activity` | View activity log |
| GET | `/admin-management/admin/<id>/performance` | View performance |
| GET | `/admin-management/reports/admins` | View reports |

## Database Tables

### admin
Stores admin user profiles with role, city assignments, and permissions.

### admin_activity_log
Audit trail of all admin actions with before/after values.

### admin_permission
Catalog of available permissions.

### admin_role
Predefined role definitions with default permissions.

## Troubleshooting

### "Only Super Admin can access this page"
- Ensure you're logged in as an admin user
- Check that your user has an Admin profile with role="super_admin"

### "You don't have permission to..."
- Check your admin role and permissions
- Regional admins have limited permissions
- Only super admins can manage other admins

### "You don't have access to this city"
- Regional admins can only access assigned cities
- Contact super admin to add your city
- Super admins can access all cities

### API Credentials Not Working
- Verify you're using the correct API key and secret
- Check if credentials were regenerated
- Ensure the admin account is active (is_active=True)

## Security Best Practices

1. **Protect API Credentials**
   - Never share API keys publicly
   - Regenerate if compromised
   - Store securely in environment variables

2. **Activity Monitoring**
   - Regularly review admin activity logs
   - Monitor approval rates
   - Check for unusual patterns

3. **Admin Management**
   - Deactivate unused admin accounts
   - Regularly audit admin permissions
   - Limit super admin access

4. **City Assignment**
   - Assign admins to specific cities
   - Prevents unauthorized access
   - Enables better tracking

## Support

For issues or questions:
1. Check the activity logs for error details
2. Review admin permissions
3. Verify database connectivity
4. Check application logs

## Next Steps

After Phase 1 completion, Phase 2 will implement:
- Mandatory onboarding for coaches
- Onboarding progress tracking
- Coin and badge rewards
- Membership system enforcement
