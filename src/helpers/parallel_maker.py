import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
def parallel_execute(num_threads, func, args):
    with ThreadPoolExecutor(max_workers=num_threads) as exc:
        fut = {exc.submit(func, *arg): i for i, arg in enumerate(args)}
        for f in as_completed(fut):
            f.result()

def make_args(num_tasks, result, data):
    length = data.shape[0]
    ids = np.arange(length)
    chunklen = (length + num_tasks - 1) // num_tasks
    chunks = [(result, data, ids[i * chunklen:(i + 1) * chunklen]) for i in range(num_tasks)]
    return chunks
    
