import os
import asyncio
import logging
import json
import MacTmp
import subprocess
from azure.iot.device import Message
from azure.iot.device.aio import IoTHubDeviceClient
logging.basicConfig(level=logging.ERROR)

model_id = "Laptop;1"

async def send_telemetry_from_laptop(device_client, telemetry_msg):
    msg = Message(json.dumps(telemetry_msg))
    print("Sent message")
    await device_client.send_message(msg)

def stdin_listener():
    while True:
        listen = 1

# Main program starts
async def main():
    # Get the environment variable
    conn_str = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")
    print(conn_str)
    print("Connecting using Connection String " + conn_str)
    device_client = IoTHubDeviceClient.create_from_connection_string(
            conn_str, product_info=model_id)
    # Connect the client
    await device_client.connect()

    # Send telemetry (current temperature and fan speed)
    async def send_telemetry():
        print("Sending telemetry for temperature")
        while True:
            temp = MacTmp.CPU_Temp()
            speed = subprocess.check_output("sudo powermetrics -i 2000 --samplers smc | grep -m 1 Fan", shell=True)
            speed = str((speed.decode("utf-8")).strip("Fan: ").strip("\n"))
            msg = {"CPUTemperature": float(temp), "CPUFanSpeed": speed}
            print(msg)
            await send_telemetry_from_laptop(device_client, msg)
            await asyncio.sleep(3)

    send_telemetry_task = asyncio.create_task(send_telemetry())

    # Run the stdin listener in the event loop
    loop = asyncio.get_running_loop()
    user_finished = loop.run_in_executor(None, stdin_listener)
    # Wait for user to indicate they are done listening for method calls
    await user_finished

    send_telemetry_task.cancel()

    # Finally, shut down the client
    await device_client.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
