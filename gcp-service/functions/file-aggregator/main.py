from google.cloud import storage
import zipfile
import os
from datetime import datetime
import pymysql

# Database settings
DB_USER = "<db_user>"
DB_PASS = "<db_password>"
DB_NAME = "<db_name>"
DB_HOST = "<db_public_ip>"

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        port=3306,
        cursorclass=pymysql.cursors.DictCursor
    )

def ensure_table_exists(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                size INT,
                created_date DATETIME
            )
        """)
        conn.commit()

def start(request):
    try:
        BUCKET_NAME = "user_uploaded_project_files"
        ZIP_BUCKET = "user_uploaded_zipped_files"
        ZIP_BUCKET_EU = "user_uploaded_project_files_eu"
        ZIP_BUCKET_REPLICATED = "user_uploaded_project_files_replicated"

        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blobs = list(bucket.list_blobs())

        if not blobs:
            return "No files found in source bucket. Skipping zip operation.", 200

        temp_dir = "/tmp/other/files"
        temp_dir_eu = "/tmp/eu/files"
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(temp_dir_eu, exist_ok=True)

        conn = get_db_connection()

        zip_path = f"/tmp/other/zipped_{datetime.now().strftime('%Y%m%d%H%M%S')}.zip"
        zip_path_eu = f"/tmp/eu/zipped_{datetime.now().strftime('%Y%m%d%H%M%S')}.zip"
        
        eu_written = False
        other_written = False

        with zipfile.ZipFile(zip_path, "w") as zipf, zipfile.ZipFile(zip_path_eu, "w") as zipf_eu:
            for blob in blobs:
                if "_eu" in os.path.splitext(blob.name)[0]:
                    local_path_eu = os.path.join(temp_dir_eu, blob.name)
                    os.makedirs(os.path.dirname(local_path_eu), exist_ok=True)
                    blob.download_to_filename(local_path_eu)
                    zipf_eu.write(local_path_eu, arcname=blob.name)
                    eu_written = True
                    
                else:
                    local_path = os.path.join(temp_dir, blob.name)
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    blob.download_to_filename(local_path)
                    zipf.write(local_path, arcname=blob.name)
                    other_written = True

                # Log to DB
                ensure_table_exists(conn)
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO file_logs (name, size, created_date) VALUES (%s, %s, %s)",
                        (blob.name, blob.size, blob.time_created)
                    )
                    conn.commit()

                # Delete from source bucket
                blob.delete()

        conn.close()

        # Upload the zip
        if other_written:
            zip_blob = client.bucket(ZIP_BUCKET).blob(os.path.basename(zip_path))
            zip_blob.upload_from_filename(zip_path)

            zip_blob_asia = client.bucket(ZIP_BUCKET_REPLICATED).blob(os.path.basename(zip_path))
            zip_blob_asia.upload_from_filename(zip_path)

        if eu_written:
            zip_blob_eu = client.bucket(ZIP_BUCKET_EU).blob(os.path.basename(zip_path_eu))
            zip_blob_eu.upload_from_filename(zip_path_eu)

        return f"Uploaded ZIP: {zip_blob.name}", 200
    
    except Exception as e:
        print("ERROR OCCURRED:", str(e))
        traceback.print_exc()
        return f"Internal Server Error: {str(e)}", 500