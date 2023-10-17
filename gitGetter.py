import os
import sys
import subprocess
import git

def getRepository(gitRepoURL : str) -> None:
    print("Removing tmp. Creating tmp. Downloading " + gitRepoURL + " there.")
    try:
        os.system("rm -R -f tmp")
    except:
        print("No tmp found.")
    os.system("mkdir tmp")
    git.Repo.clone_from(gitRepoURL, "tmp/")

if __name__ == "__main__":
    getRepository(sys.argv[1])
