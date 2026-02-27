import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Missing Supabase credentials in environment variables")
    exit(1)

supabase: Client = create_client(url, key)

email = "judge@neutrino.dev"
password = "Demo2026!"

try:
    # Service role key can create users directly and bypass confirmation
    res = supabase.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True
    })
    print(f"User {email} created successfully!")
except Exception as e:
    err_str = str(e)
    if "already exists" in err_str.lower() or "already been registered" in err_str.lower() or "user_already_exists" in err_str:
        print(f"User {email} already exists. Attempting to update password if needed.")
        try:
            # We can't fetch the user uid easily by email using Python supabase client without listing users
            # The admin api supports listing users:
            users_res = supabase.auth.admin.list_users()
            user_id = next((u.id for u in users_res if u.email == email), None)
            
            if user_id:
                supabase.auth.admin.update_user_by_id(user_id, {"password": password})
                print(f"Password for {email} updated successfully!")
            else:
                print("Could not find user ID to update password.")
        except Exception as update_e:
            print(f"Failed to update user: {update_e}")
    else:
        print(f"Failed to create user: {e}")
