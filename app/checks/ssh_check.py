import socket
import time


def verificar_ssh(host: str, porta: int = 22, timeout: int = 5):
    inicio = time.time()

    try:
        with socket.create_connection((host, porta), timeout=timeout):
            fim = time.time()

            return {
                "sucesso": True,
                "tempo_resposta": int((fim - inicio) * 1000),
                "mensagem": "SSH OK"
            }

    except Exception as e:
        fim = time.time()

        return {
            "sucesso": False,
            "tempo_resposta": int((fim - inicio) * 1000),
            "mensagem": str(e)
        }