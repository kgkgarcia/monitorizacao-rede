import requests
import time


def verificar_http(url: str, timeout: int = 5):
    inicio = time.time()

    try:
        response = requests.get(url, timeout=timeout)
        tempo = int((time.time() - inicio) * 1000)

        if response.status_code < 400:
            return {
                "sucesso": True,
                "tempo_resposta": tempo,
                "mensagem": f"HTTP {response.status_code}"
            }
        else:
            return {
                "sucesso": False,
                "tempo_resposta": tempo,
                "mensagem": f"HTTP erro {response.status_code}"
            }

    except Exception as e:
        return {
            "sucesso": False,
            "tempo_resposta": None,
            "mensagem": str(e)
        }