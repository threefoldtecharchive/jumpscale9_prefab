from js9 import j
import os
import time

farmer_id = os.environ.get('FARMER_ID')
if not farmer_id:
    print("can't find FARMER ID in environment, exiting")

logger = j.logger.get('zbundle_capacity')

try:
    while True:
        data = j.sal.ubuntu.capacity.get(farmer_id)
        client = j.clients.grid_capacity.get(interactive=False)
        _, resp = client.api.RegisterCapacity(data)
        if resp.status_code == 201:
            logger.info("capacity registered")
        else:
            logger.error("error during registration...")
        time.sleep(10 * 60)  # every 10 minutes
except KeyboardInterrupt:
    pass
