from champions_tavily.tavily_upload_champions import upload_champions_to_s3
from sample_fanfiction.sample_fanfiction_upload import upload_sample_fanfiction_to_s3

def data_extraction_flow():
    print ("Starting data extraction flow ...\n")

    print ("Uploading champions to S3 using tavily...\n")
    upload_champions_to_s3()

    print ("\nData extraction flow completed\n.")

    print ("Uploading sample fanfiction to S3...\n")
    upload_sample_fanfiction_to_s3()    
    print ("\nData extraction flow completed.\n")

if __name__ == "__main__":
    data_extraction_flow()