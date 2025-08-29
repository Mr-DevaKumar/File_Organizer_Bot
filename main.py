# main.py
#!/usr/bin/env python3
import argparse
import logging
from organizer import FileOrganizer
from scheduler import OrganizerScheduler

def main():
    parser = argparse.ArgumentParser(description="File Organizer Bot")
    parser.add_argument("--config", "-c", default="config.yaml", 
                       help="Path to config file")
    parser.add_argument("--dry-run", "-d", action="store_true",
                       help="Show what would be done without moving files")
    parser.add_argument("--schedule", "-s", action="store_true",
                       help="Run as a scheduled service")
    parser.add_argument("--once", "-o", action="store_true",
                       help="Run once and exit")
    
    args = parser.parse_args()
    
    if args.schedule:
        # Run as scheduled service
        scheduler = OrganizerScheduler(args.config)
        scheduler.run_continuously()
    elif args.once:
        # Run once
        organizer = FileOrganizer(args.config)
        organizer.organize_files(dry_run=args.dry_run)
    else:
        # Interactive mode
        organizer = FileOrganizer(args.config)
        print("File Organizer Bot - Interactive Mode")
        print("=====================================")
        
        while True:
            print("\nOptions:")
            print("1. Run organization (dry run)")
            print("2. Run organization (actual move)")
            print("3. Exit")
            
            choice = input("Enter your choice (1-3): ").strip()
            
            if choice == "1":
                organizer.organize_files(dry_run=True)
            elif choice == "2":
                organizer.organize_files(dry_run=False)
            elif choice == "3":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()