from recon_engine.recon.recon_engine import ReconEngine
from recon_engine.config import recon_settings
from datetime import datetime, date
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReconScheduler:
    def __init__(self):
        self.recon_engine = ReconEngine()
        self.completed_jobs = set()  # Track jobs completed today
        self.last_date = None
        
    def _reset_daily_tracking(self):
        """Reset tracking when date changes"""
        current_date = date.today()
        if self.last_date != current_date:
            self.completed_jobs.clear()
            self.last_date = current_date
            logger.info(f"Reset daily job tracking for {current_date}")
    
    def _should_run_scheduler(self):
        """Check if current hour matches configured scheduler hour"""
        current_hour = datetime.now().hour
        target_hour = recon_settings.scheduler_hour
        return current_hour == target_hour
    
    def _get_job_key(self, source, run_date):
        """Generate unique key for job tracking"""
        return f"{source}_{run_date}"
    
    async def _run_recon_for_source(self, source):
        """Run reconciliation for a specific source"""
        today = date.today()
        job_key = self._get_job_key(source, today)
        
        if job_key in self.completed_jobs:
            logger.info(f"Skipping {source} - already completed today")
            return
        
        try:
            logger.info(f"Starting reconciliation for source: {source}")
            await self.recon_engine.run(date=today, source=source)
            
            # Mark as completed
            self.completed_jobs.add(job_key)
            logger.info(f"Successfully completed reconciliation for source: {source}")
            
        except Exception as e:
            logger.error(f"Failed to run reconciliation for source {source}: {str(e)}")
    
    async def _run_all_sources(self):
        """Run reconciliation for all configured sources"""
        if not hasattr(recon_settings, 'sources') or not recon_settings.sources:
            logger.warning("No sources configured for reconciliation")
            return
        
        logger.info(f"Starting reconciliation for {len(recon_settings.sources)} sources")
        
        # Run all sources concurrently
        tasks = []
        for source in recon_settings.sources:
            task = asyncio.create_task(self._run_recon_for_source(source))
            tasks.append(task)
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("Completed reconciliation run for all sources")
    
    async def start(self):
        """Start the infinite scheduling loop"""
        logger.info(f"Starting reconciliation scheduler - will run at hour {recon_settings.scheduler_hour}")
        
        while True:
            try:
                # Reset daily tracking if date changed
                self._reset_daily_tracking()
                
                # Check if we should run the scheduler
                if self._should_run_scheduler():
                    logger.info("Scheduler time reached - starting reconciliation")
                    await self._run_all_sources()
                
                # Wait for 60 seconds before next check
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                # Continue running even if there's an error
                await asyncio.sleep(60)

# Main entry point
async def main():
    scheduler = ReconScheduler()
    await scheduler.start()

if __name__ == "__main__":
    asyncio.run(main())