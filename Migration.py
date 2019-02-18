from ArtifactoryHandler import ArtifactoryHandler
from progressbar import ProgressBar
import Queue
import configparser
import csv
from datetime import datetime

def processCsv(src_ah):
    checked_path = []
    all_path = Queue.Queue()

    # Read files to all_path
    with open('path.csv') as csv_file:
        reader = csv.reader(csv_file, delimiter = ',')
        line = 1
        for row in reader:
            # Not header
            if line != 1 :
                row = {'src':processPath(row[0]),'des':processPath(row[1])}
                all_path.put(row)
            line += 1

    # Add all and sub-folders to checked_src_path
    while not all_path.empty():
        path = all_path.get()
        checked_path.append(path)
        folderInfo = src_ah.getFolderInfo(path.get('src'))
        if not folderInfo:
            print (str(datetime.now()) + ': Line 27, getting folder failed, path: ' + path.get('src'))
        else:
            for children in folderInfo.get('children'):
                # It has sub-folder
                if children.get('folder') == True:
                    temp = {}
                    temp['src'] = path.get('src')+children.get('uri')
                    temp['des'] = path.get('des')+children.get('uri')
                    all_path.put(temp)
    
    return checked_path

def migration(src_ah, des_ah, paths):
    pbar = ProgressBar()
    for path in pbar(paths):
        # Get artifact names in that folder
        artifacts = []
        folderInfo = src_ah.getFolderInfo(path.get('src'))
        if not folderInfo:
            print (str(datetime.now()) + ': Line 46, getting folder failed, path: ' + path.get('src'))
        else:
            for children in folderInfo.get('children'):
                if children.get('folder') == False:
                    artifacts.append(children.get('uri'))

            # Download artifacts to the folder
            for artifact in artifacts:
                r_down = src_ah.retrieveArtifacts(path.get('src'), artifact[1:])
                if r_down.status_code != 200:
                    print (str(datetime.now()) + ': Line 56, downloading artifacts failed, path: ' + path.get('src'))

            # Upload artifacts to the destination artifactory
            for artifact in artifacts:
                r_up = des_ah.deployArtifacts(path.get('des'),artifact[1:])
                if r_up.status_code != 201:
                    print (str(datetime.now()) + ': Line 62, uploading artifacts failed, path: ' + path.get('src'))

    

def processPath(path):
    if path[0] != '/':
        path = '/' + path
    if path [-1] == '/':
        path = path[:-1]
    return path


if __name__== "__main__":
    # Set up the variables
    config = configparser.ConfigParser()
    config.read('config.modern') # Change this in the server!
    src_art = config['migration']['src_art']
    des_art = config['migration']['des_art']
    src_art_url = config[src_art]['url']
    src_art_username = config[src_art]['username']
    src_art_password = config[src_art]['password']
    des_art_url = config[des_art]['url']
    des_art_username = config[des_art]['username']
    des_art_password = config[des_art]['password']

    # Initialize the two handlers
    src_ah = ArtifactoryHandler(src_art_username,src_art_password,src_art_url)
    des_ah = ArtifactoryHandler(des_art_username,des_art_password,des_art_url)

    paths = processCsv(src_ah)
    migration(src_ah, des_ah, paths)


