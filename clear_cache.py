
import os
import shutil

def clear_cache():
    # Define cache directories
    cache_dirs = ['/path/to/cache/dir1', '/path/to/cache/dir2']

    # Iterate through each cache directory
    for dir in cache_dirs:
        try:
            # Attempt to delete the directory and its contents
            shutil.rmtree(dir)
            print(f'Cleared cache from {dir}')
        except FileNotFoundError:
            print(f'Cache directory {dir} not found')

def main():
    clear_cache()

if __name__ == '__main__':
    main()
