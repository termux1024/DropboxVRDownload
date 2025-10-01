import runpy

# Run CheckDropboxDownloads.py first to generate missing_links.txt
runpy.run_path("CheckDropboxDownloads.py")

# Then run BatchDropboxDownloader.py to download missing links
runpy.run_path("BatchDropboxDownloader.py")