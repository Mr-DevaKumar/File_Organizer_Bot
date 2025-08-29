# scheduler.py
import schedule
import time
import logging
from organizer import FileOrganizer

class OrganizerScheduler:
    def __init__(self, config_path: str = "config.yaml"):
        self.organizer = FileOrganizer(config_path)
        self.schedule_jobs()
    
    def schedule_jobs(self):
        """Schedule organization jobs"""
        # Run every hour
        schedule.every().hour.do(self.run_organization)
        
        # Additional schedules can be added here
        # schedule.every().day.at("10:30").do(self.run_organization)
        # schedule.every().monday.do(self.run_organization)
    
    def run_organization(self):
        """Run the organization process"""
        logging.info("Scheduled organization started")
        try:
            self.organizer.organize_files()
        except Exception as e:
            logging.error(f"Error during scheduled organization: {e}")
        logging.info("Scheduled organization completed")
    
    def run_continuously(self):
        """Run the scheduler continuously"""
        logging.info("Scheduler started. Press Ctrl+C to exit.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logging.info("Scheduler stopped by user")