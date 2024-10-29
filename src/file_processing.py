#!/usr/bin/env python3

import os
import shutil

from termcolor import colored

from corpo_chatbot.settings import BASE_DIR

allowed_files = ["pdf"]


# Method to check pdf files
def files_in_docs():
    print(colored(f"\n[+] Loocking for files on: ./docs", "red"))
    print(colored(f"\n[+] files:\n", "red"))
    path = os.path.join(BASE_DIR, "./docs/")
    files = os.listdir(path)
    files.remove("ignore_this_file.txt")
    print(colored(files, "blue"))
    return files
