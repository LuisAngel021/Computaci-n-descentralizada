import socket
import pickle
import numpy as np
import time
import threading
from queue import Queue

# Función para distribuir las filas de la matriz entre los nodos
def distribute_matrix_rows(matrix, num_procs):
    rows_per_proc = len(matrix) // num_procs
    remainder = len(matrix) % num_procs
    rows = []
    start = 0
    for i in range(num_procs):
        end = start + rows_per_proc + (1 if i < remainder else 0)
        rows.append(matrix[start:end])
        start = end
    return rows

# Función para realizar la multiplicación de matrices
def matrix_multiplication(A, B):
    result = np.zeros((A.shape[0], B.shape[1]))
    for i in range(A.shape[0]):
        for j in range(B.shape[1]):
            for k in range(A.shape[1]):
                result[i][j] += A[i][k] * B[k][j]
    return result

# Función para enviar grandes cantidades de datos
def send_large_data(socket, data):
    data = pickle.dumps(data)
    size = len(data)
    socket.sendall(size.to_bytes(4, 'big'))
    socket.sendall(data)

# Función para recibir grandes cantidades de datos
def receive_large_data(socket):
    size = int.from_bytes(socket.recv(4), 'big')
    data = b""
    while len(data) < size:
        packet = socket.recv(4096)
        if not packet:
            break
        data += packet
    return pickle.loads(data)

# Función para enviar una tarea a un nodo
def send_task(task, node_ip, node_port=9999):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((node_ip, node_port))
        send_large_data(client_socket, task)
        result = receive_large_data(client_socket)
        client_socket.close()
        return result
    except Exception as e:
        print(f"Error al comunicarse con {node_ip}: {e}")
        return None

# Función que ejecuta cada hilo de trabajo
def worker_thread(ip, task_queue, results, lock, active_nodes, replacements):
    while not task_queue.empty():
        try:
            task = task_queue.get()
            result = send_task(task, ip)
            if result is not None:
                with lock:
                    results.append(result)
                task_queue.task_done()
            else:
                with lock:
                    task_queue.put(task)
                    active_nodes.remove(ip)
                    break
        except Exception as e:
            print(f"Error al procesar la tarea en {ip}: {e}")
            with lock:
                task_queue.put(task)

if __name__ == "__main__":
    # Inicialización de matrices A y B
    A = np.random.randint(0, 10, (500, 500))
    B = np.random.randint(0, 10, (500, 500))

    # Direcciones IP de los nodos esclavos
    ips = ['192.168.1.2', '192.168.1.3', '192.168.1.4']
    port = 9999

    # Tiempo de inicio
    start_time = time.time()

    # Distribuir las filas de la matriz A entre los nodos
    rows = distribute_matrix_rows(A, len(ips) + 1)
    local_result = matrix_multiplication(np.array(rows[0]), B)

    # Cola de tareas para manejar las filas de la matriz
    task_queue = Queue()
    for row in rows[1:]:
        task_queue.put((row, B))

    # Resultados y configuraciones de hilos
    results = [local_result]
    total_tasks = len(rows) - 1

    lock = threading.Lock()
    active_nodes = set(ips)
    replacements = {}
    threads = []

    # Crear y iniciar hilos de trabajo
    for ip in ips:
        thread = threading.Thread(target=worker_thread, args=(ip, task_queue, results, lock, active_nodes, replacements))
        thread.start()
        threads.append(thread)

    # Esperar a que todos los hilos terminen
    for thread in threads:
        thread.join()

    # Reintentar tareas restantes con nodos activos
    while not task_queue.empty() and active_nodes:
        failed_node = None
        for ip in ips:
            if ip not in active_nodes:
                failed_node = ip
                break
        
        if failed_node:
            replacement_node = active_nodes.pop()
            print(f"El nodo {failed_node} se ha desconectado. Reasignando tareas pendientes al nodo {replacement_node}")
            replacements[failed_node] = replacement_node
            thread = threading.Thread(target=worker_thread, args=(replacement_node, task_queue, results, lock, active_nodes, replacements))
            thread.start()
            threads.append(thread)

    # Esperar a que todos los hilos terminen
    for thread in threads:
        thread.join()

    # Unir resultados finales
    final_result = np.vstack(results)

    # Tiempo de fin y mostrar resultados
    end_time = time.time()

    print("Resultado de la multiplicación de matrices:")
    print(final_result)
    print(f"Tiempo total de cálculo: {end_time - start_time} segundos")

