"""
############################
# 1st phase - all in 1 app #
############################
1. flask hello world

2. add other flask endpoints

3. hard code responses

4. look up how to accept only POST (GET is default)

5. return html for GET /
<form method="post" enctype="multipart/form-data" action="/upload" method="post">
  <div>
    <label for="file">Choose file to upload</label>
    <input type="file" id="file" name="form_file" accept="image/jpeg"/>
  </div>
  <div>
    <button>Submit</button>
  </div>
</form>

6. in GET /files return a hardcoded list for initial testing
files = ['file1.jpeg', 'file2.jpeg', 'file3.jpeg']

7. in GET / call the function for GET /files and loop through the list to add to the HTML
GET /
    ...
    for file in list_files():
        index_html += "<li><a href=\"/files/" + file + "\">" + file + "</a></li>"

    return index_html

8. in POST /upload - lookup how to extract uploaded file and save locally to ./files
def upload():
    file = request.files['form_file']  # item name must match name in HTML form
    file.save(os.path.join("./files", file.filename))

    return redirect("/")
#https://flask.palletsprojects.com/en/2.2.x/patterns/fileuploads/

9. in GET /files - look up how to list files in a directory

    files = os.listdir("./files")
    #TODO: filter jpeg only
    return files

10. filter only .jpeg
@app.route('/files')
def list_files():
    files = os.listdir("./files")
    for file in files:
        if not file.endswith(".jpeg"):
            files.remove(file)
    return files
"""
import os
import sys
import traceback
from flask import Flask, redirect, request, send_file
from google.cloud import storage

# Initialize Google Cloud Storage client
storage_client = storage.Client()
bucket_name = "sutcliff-fau-cloud-native"

# Ensure local storage for temporary files
os.makedirs('files', exist_ok=True)

app = Flask(__name__)

def get_list_of_files(bucket_name):
    """Lists all the blobs in the bucket."""
    blobs = storage_client.list_blobs(bucket_name)
    return [blob.name for blob in blobs]

def upload_file(bucket_name, file_path):
    """Uploads a file to the bucket."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(os.path.basename(file_path))
    blob.upload_from_filename(file_path)

def download_file(bucket_name, file_name):
    """Downloads a file from the bucket to the local directory."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.download_to_filename(os.path.join("files", file_name))
    return os.path.join("files", file_name)

@app.route('/')
def index():
    """Main page with upload form and list of files."""
    index_html = """
    <form method="post" enctype="multipart/form-data" action="/upload">
      <div>
        <label for="file">Choose file to upload</label>
        <input type="file" id="file" name="form_file" accept="image/jpeg"/>
      </div>
      <div>
        <button>Submit</button>
      </div>
    </form>
    <ul>
    """
    
    for file in get_list_of_files(bucket_name):
        if file.lower().endswith(('.jpeg', '.jpg')):
            index_html += f'<li><a href="/files/{file}">{file}</a></li>'
    
    index_html += "</ul>"
    return index_html

@app.route('/upload', methods=["POST"])
def upload():
    """Handles file upload and stores it in Google Cloud Storage."""
    file = request.files['form_file']
    temp_path = os.path.join("files", file.filename)
    file.save(temp_path)
    upload_file(bucket_name, temp_path)
    os.remove(temp_path)  # Clean up local storage
    return redirect("/")

@app.route('/files')
def list_files():
    """Lists available JPEG files stored in Google Cloud Storage."""
    files = get_list_of_files(bucket_name)
    jpegs = [file for file in files if file.lower().endswith(('.jpeg', '.jpg'))]
    return "<ul>" + "".join(f"<li><a href='/files/{file}'>{file}</a></li>" for file in jpegs) + "</ul>"

@app.route('/image/<filename>')
def get_image(filename):
    print("GET /image/" + filename)
    return send_file(os.path.join("./files", filename))

@app.route('/files/<filename>')
def get_file(filename):
    """Retrieves a file from Google Cloud Storage and displays it in the browser."""
    print("GET /files/" + filename)
    file_path = download_file(bucket_name, filename)
    image_html = f"<h2>{filename}</h2>" + \
                 f'<img src="/image/{filename}" width="500" height="333">'
    return image_html

if __name__ == '__main__':
    app.run(debug=True)