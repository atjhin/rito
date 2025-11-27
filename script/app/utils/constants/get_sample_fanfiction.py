from app.database.fetch_from_s3 import get_sample_fanfiction_from_s3

def get_sample_fanfiction():
    """
    Fetch sample fanfiction from S3.
    
    Returns:
        Sample fanfiction text
    """
    fanfiction = get_sample_fanfiction_from_s3()
    
    if not fanfiction:
        return "No sample fanfiction available."
    
    return fanfiction['content']