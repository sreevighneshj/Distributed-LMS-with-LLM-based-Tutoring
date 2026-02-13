from menu import *
from functions import *
from imports import *
from grpc_calls import *
import grpc
import time




if __name__ == '__main__':
    while True:
        # Step 1: Get the leader ID from the bootstrap servers
        leader_id = get_leader_id()

        # Step 2: If leader ID is found, map it to the correct host and port
        if leader_id:
            leader_host, leader_port = get_leader_host_port(leader_id)

            if leader_host and leader_port:
                # Step 3: Attempt to connect to the leader using the host and port
                channel = connect_to_leader(leader_host, leader_port)
                if channel:
                    # Step 4: Handle the main menu if connection to leader is successful
                    handle_menu(main_menu_options, main_menu_action, "Main Menu")

                    break  # Exit the loop once connected and menu is handled
            else:
                print("Leader ID not found in node information, retrying...")
        else:
            print("Retrying to get the leader...")

        # Step 5: Wait before retrying to get leader info
        time.sleep(LEADER_RETRY_DELAY)
