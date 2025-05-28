#!/usr/bin/env python3
"""
Cleanup script to remove redundant files and secure the project
"""
import os
import shutil
from pathlib import Path

def cleanup_project():
    """Remove redundant files and secure sensitive data"""
    
    print("🧹 Cleaning up redundant files and securing the project...")
    print("=" * 50)
    
    # Files to remove
    files_to_remove = [
        "backend/spotify_auth.py",  # Redundant auth script
        "auth_spotify.py",           # Redundant auth script
        ".env.backup"                # SECURITY: Contains exposed credentials
    ]
    
    # Process each file
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Removed: {file_path}")
            except Exception as e:
                print(f"❌ Failed to remove {file_path}: {str(e)}")
        else:
            print(f"⚪ Not found: {file_path}")
    
    # Rename auth_spotify_fixed.py to auth_spotify.py
    if os.path.exists("auth_spotify_fixed.py"):
        try:
            shutil.move("auth_spotify_fixed.py", "auth_spotify.py")
            print(f"✅ Renamed: auth_spotify_fixed.py → auth_spotify.py")
        except Exception as e:
            print(f"❌ Failed to rename auth_spotify_fixed.py: {str(e)}")
    
    # Update .gitignore
    print("\n📝 Updating .gitignore...")
    gitignore_additions = [
        "\n# Security - Never commit these",
        ".env.backup",
        ".env.*",
        "*.env",
        "\n# Spotify authentication cache",
        ".spotify_cache*",
        ".cache-*"
    ]
    
    try:
        with open(".gitignore", "a") as f:
            f.write("\n")
            for line in gitignore_additions:
                f.write(line + "\n")
        print("✅ Updated .gitignore with security rules")
    except Exception as e:
        print(f"❌ Failed to update .gitignore: {str(e)}")
    
    print("\n⚠️  IMPORTANT SECURITY ACTIONS REQUIRED:")
    print("=" * 50)
    print("Your API keys were exposed in .env.backup!")
    print("\n1. Regenerate your Groq API key:")
    print("   → Visit: https://console.groq.com/keys")
    print("\n2. Regenerate your Spotify credentials:")
    print("   → Visit: https://developer.spotify.com/dashboard")
    print("   → Select your app → Settings → Regenerate client secret")
    print("\n3. Update your .env file with the new credentials")
    print("\n4. If this was committed to git, consider:")
    print("   → git rm --cached .env.backup")
    print("   → git commit -m 'Remove sensitive data'")
    print("   → Consider using git-filter-branch or BFG to remove from history")
    
    print("\n✨ Cleanup complete!")

if __name__ == "__main__":
    try:
        response = input("This will remove redundant files. Continue? (Y/n): ").strip().lower()
        if response != 'n':
            cleanup_project()
        else:
            print("👋 Cleanup cancelled.")
    except KeyboardInterrupt:
        print("\n\n👋 Cleanup cancelled by user.")