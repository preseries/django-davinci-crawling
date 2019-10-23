################################
Start Docker Instances for crawl
################################

- Example to start a VM from python

https://medium.com/google-cloud/using-app-engine-to-start-a-compute-engine-vm-be713c98d6a
https://github.com/fivunlm/app-engine-start-vm/blob/master/main.py

- Container Optimized OS instances

https://cloud.google.com/container-optimized-os/docs/how-to/run-container-instance
https://cloud.google.com/container-optimized-os/docs/how-to/create-configure-instance 


Init instances:
===============

- Cloud-init to start the docker container instance)

    https://cloud.google.com/container-optimized-os/docs/how-to/create-configure-instance#viewing_available_images

- or, Startup script

    https://cloud.google.com/compute/docs/startupscript
    
    
Proxies Support
===============

- Rotating proxies utilities:
    - For Scrappy (we can extract ideas) https://github.com/TeamHG-Memex/scrapy-rotating-proxies
    - The S1mbi0se proxy for conclas project: https://github.com/s1mbi0se/conclas/blob/master/conclas/miner/proxy.py 
    
- Obtain lists of proxies (free)
    - FREE: list-proxies node module made exactly for that: https://github.com/chill117/proxy-lists it generates a proxy file that can be used by the previous rotation proxy code.
    - https://proxymesh.com