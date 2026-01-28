import shutil

def delete_folder(name):
    try:
        shutil.rmtree(name)
    except:
        pass