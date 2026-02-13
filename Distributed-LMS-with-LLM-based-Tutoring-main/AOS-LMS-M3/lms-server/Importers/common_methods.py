
from Importers.common_imports import *

def sha256_hash(obj):
    return hashlib.sha256(obj.encode()).hexdigest()

def getTimestamp():
    return datetime.now().strftime("%Y%m%d%H%M%S")

def get_uuid():
    return str(uuid.uuid4())

def zip_files_in_directory(directory_path):
    # Create a BytesIO object to store the zip file in memory
    zip_buffer = BytesIO()

    # Create a ZipFile object, writing to the BytesIO object
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Iterate over all files in the directory
        for file_name in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file_name)
            if os.path.isfile(file_path):
                # Write each file into the zip file, using its relative path
                zip_file.write(file_path, arcname=file_name)

    # Set the file pointer to the beginning of the BytesIO object
    zip_buffer.seek(0)

    return zip_buffer.getvalue()