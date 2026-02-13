

def some_func():
    pass



def handle_menu(options,actions,head):
    while True:
        print(f"==== {head} ====")
        id_list = []
        for id,name in options:
            id_list.append(id)
            print(f"[{id}] {name}")
        print("[0] Exit")

        opted = int(input("Select menu option: "))
        if opted not in id_list:
            print("Invalid option")
        if opted == 0:
            print("Exiting...")
            return None,True

        action = actions.get(opted)
        if not action and opted != 0:
            print("Invalid option")
        further_menu, terminate = action()
        if terminate:
            print(f"Exiting...")
            return
        if further_menu:
            handle_menu(**further_menu)



