import time
import puresnmp


def verificar_snmp(host: str, comunidade: str, oid: str, porta: int = 161, timeout: int = 5):
    inicio = time.time()
    try:
        valor = puresnmp.get(host, comunidade, oid, port=porta)
        tempo = int((time.time() - inicio) * 1000)

        return {
            "sucesso": True,
            "tempo_resposta": tempo,
            "valor": str(valor),
            "mensagem": "SNMP OK"
        }

    except Exception as e:
        return {
            "sucesso": False,
            "tempo_resposta": int((time.time() - inicio) * 1000),
            "valor": None,
            "mensagem": str(e)
        }