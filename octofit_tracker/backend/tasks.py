from celery import shared_task
from .data_pipeline import DataPipeline

@shared_task
def run_data_pipeline():
    """Run the data pipeline as a background task."""
    pipeline = DataPipeline(mongo_uri='mongodb://localhost:27017', db_name='octofit')
    raw_data = pipeline.fetch_data('raw_data')
    processed_data = pipeline.process_data(raw_data)
    pipeline.save_results('processed_data', processed_data)
