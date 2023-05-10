import modules.scripts as scripts
import gradio as gr
import os
import shutil
from zipfile import ZipFile

from modules import script_callbacks


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), 
                       os.path.relpath(os.path.join(root, file), 
                                       os.path.join(path, '..')))

def download_files(folder_name):
    cwd = os.getcwd()
    folder_zip = cwd + '/' + folder_name + '/'
    if os.path.isdir(folder_zip) == False:
        return "folder path not exist, please correct it!", None
    try: 
        with ZipFile("tmp.zip", "w") as zipObj:
            zipdir(folder_zip, zipObj)
    except Exception as e:
        return " zip file failed!", None
    else:
        return "generate zip file successful!", "tmp.zip"

def upload_files(folder_name,files):
    cwd = os.getcwd()
    folder_save = cwd + '/' + folder_name + '/'
    if os.path.isdir(folder_save) == False:
         os.mkdir(folder_name)
    try:
        for idx, file in enumerate(files):
            print(file.name)
            shutil.copy(file.name, cwd + '/' + folder_name + '/' + file.name.rsplit('/', 1)[-1])
    except Exception as e:
         return str(e)
    else:
         return "upload files successfully to " + folder_name + " !"

def on_ui_tabs():
    upload = gr.Interface(
        upload_files,
        [gr.Textbox(placeholder="please input your destination folder name!"), gr.File(file_count="directory")],
        "text"
    )

    download = gr.Interface(
        download_files,
        gr.Textbox(placeholder="please input your source folder name!"),
        ["text","file"]
    )

    app = gr.TabbedInterface([upload, download], ["upload", "download"])

    return [(app, "UpDownload", "extension_template_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)
