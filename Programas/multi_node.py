import socket
import threading
import pickle
import numpy as np

def matrix_multiplication(A, B):
    result = np.zeros((A.shape[0], B.shape[1]))
    for i in range(A.shape[0]):
        for j in range(B.shape[1]):
            for k in range(A.shape[1]):
                result[i][j] += A[i][k] * B[k][j]
    return result

def send_large_data(socket, data):
    data = pickle.dumps(data)
    size = len(data)
    socket.sendall(size.to_bytes(4, 'big'))
    socket.sendall(data)

def receive_large_data(socket):
    size = int.from_bytes(socket.recv(4), 'big')
    data = b""
    while len(data) < size:
        packet = socket.recv(4096)
        if not packet:
            break
        data += packet
    return pickle.loads(data)

def handle_client(client_socket):
    A, B = receive_large_data(client_socket)
    result = matrix_multiplication(A, B)
    send_large_data(client_socket, result)
    client_socket.close()

def server():
    server_ip = '0.0.0.0'  # Escuchar en todas las interfaces de red
    server_port = 9999
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_ip, server_port))
    server_socket.listen(5)
    
    print(f"Servidor escuchando en {server_ip}:{server_port}")
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Conexión aceptada de {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    server()

