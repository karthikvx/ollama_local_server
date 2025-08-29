run ollama local on linux
text parser on docker
web ui to intake file and process thru available models in local

'''

docker run --rm -p 5000:5000 -v ~/Pictures/Screenshots:/root/Pictures/Screenshots -v $(pwd)/output-folder:/app/output-folder img2text




docker run --rm -v ~/Pictures/Screenshots:/root/Pictures/Screenshots -v $(pwd)/output-folder:/app/output-folder img2text python pngs_to_md.py

'''


karthikvx@gmail.com


one file  ( my-applications ) has the jobs applied and second file (search-jobs) has current job list. exclude jobs in my-applications from search-jobs, exclude my-applications inactive jobs titles from search-jobs. group the output result by location   