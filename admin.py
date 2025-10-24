# admin.py
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash

from app import User

def create_admin_user():
    """Create an admin user in the database"""
    
    admin_username = input("Enter the Username: ")
    admin_email = input("Enter the Email Address: ")
    admin_password = input("Enter the password: ")  # You can change this default password
    admin_first_name = "Super"
    admin_last_name = "Admin"
    
    try:
        # Check if admin user already exists
        existing_admin = User.objects(username=admin_username).first()
        if existing_admin:
            print(f"❌ Admin user '{admin_username}' already exists!")
            print(f"   User ID: {existing_admin.id}")
            print(f"   Email: {existing_admin.email}")
            return False
        
        # Hash the password using werkzeug.security
        hashed_password = generate_password_hash(admin_password)
        
        # Create admin user
        admin_user = User(
            username=admin_username,
            email=admin_email,
            password_hash=hashed_password,
            first_name=admin_first_name,
            last_name=admin_last_name,
            user_type="admin",
            is_active=True,
            is_verified=True
        )
        
        admin_user.save()
        
        print("✅ Admin user created successfully!")
        print(f"   Username: {admin_username}")
        print(f"   Email: {admin_email}")
        print(f"   Password: {admin_password}")
        print(f"   User Type: admin")
        print(f"   User ID: {admin_user.id}")
        print("\n⚠️  Please change the default password after first login!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        return False

def list_all_users():
    """List all users in the database"""
    try:
        users = User.objects()
        print(f"\n📋 Total Users: {users.count()}")
        print("-" * 80)
        print(f"{'Username':<15} {'Email':<25} {'User Type':<10} {'Status':<8}")
        print("-" * 80)
        
        for user in users:
            status = "Active" if user.is_active else "Inactive"
            print(f"{user.username:<15} {user.email:<25} {user.user_type:<10} {status:<8}")
            
    except Exception as e:
        print(f"❌ Error listing users: {str(e)}")

def delete_user(username):
    """Delete a user by username"""
    try:
        user = User.objects(username=username).first()
        if not user:
            print(f"❌ User '{username}' not found!")
            return False
        
        user.delete()
        print(f"✅ User '{username}' deleted successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error deleting user: {str(e)}")
        return False

def change_admin_password():
    """Change admin user password"""
    try:
        admin_user = User.objects(username="admin", user_type="admin").first()
        if not admin_user:
            print("❌ Admin user not found!")
            return False
        
        new_password = input("Enter new password for admin: ").strip()
        if not new_password:
            print("❌ Password cannot be empty!")
            return False
        
        # Hash the new password
        hashed_password = generate_password_hash(new_password)
        admin_user.password_hash = hashed_password
        admin_user.save()
        
        print("✅ Admin password changed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error changing password: {str(e)}")
        return False

def show_menu():
    """Display the admin management menu"""
    print("\n" + "="*50)
    print("        ADMIN USER MANAGEMENT")
    print("="*50)
    print("1. Create Admin User")
    print("2. List All Users")
    print("3. Change Admin Password")
    print("4. Delete User")
    print("5. Exit")
    print("="*50)

if __name__ == "__main__":
    import getpass
    
    print("🔧 Admin User Management Tool")
    print("   Using werkzeug.security for password hashing")
    
    while True:
        show_menu()
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            create_admin_user()
            
        elif choice == '2':
            list_all_users()
            
        elif choice == '3':
            change_admin_password()
            
        elif choice == '4':
            username = input("Enter username to delete: ").strip()
            if username:
                delete_user(username)
            else:
                print("❌ Please enter a valid username!")
                
        elif choice == '5':
            print("👋 Exiting...")
            break
            
        else:
            print("❌ Invalid choice! Please enter 1-5.")
        
        input("\nPress Enter to continue...")