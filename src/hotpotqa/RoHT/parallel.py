import concurrent.futures, random, time

# def handle_item(data):
#     waiting = random.random() * 3 + 1
#     print("Thread %d, Waiting %.2f ..."%(data, waiting))
#     time.sleep(waiting)
#     if random.random() < 0.5:
#         raise Exception()
#     print("Thread %d, OK."%(data))

# def parallel_process_data(data, handle_item, workers=20, callback=None):
#     with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
#         futures = []
#         for item in data:
#             future = executor.submit(handle_item, item)
#             futures.append(future)
#         for future in concurrent.futures.as_completed(futures):
#             result = future.result()
#             if callback:
#                 callback(result)

# if __name__ == "__main__":
#     parallel_process_data([i for i in range(20)], handle_item)   
#     print("end") 

def parallel_process_data(data, handle_item, workers=20, callback=None):
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(handle_item, item): item for item in data}

        for future in concurrent.futures.as_completed(futures):
            item = futures[future]
            try:
                future.result()  # Get result or raise exception
                if callback:
                    callback(item)
            except Exception as e:
                print(f"Task {item} raised an exception: {e}")
