import os
import socket
import qrcode

def ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # não envia nada, só descobre a interface de rede em uso
        return s.getsockname()[0]
    finally:
        s.close()

# caminho relativo à pasta deste arquivo, e não à pasta do terminal
pasta_projeto = os.path.dirname(os.path.abspath(__file__))
caminho_qrcode = os.path.join(pasta_projeto, "static", "qrcode.png")
os.makedirs(os.path.dirname(caminho_qrcode), exist_ok=True)

url = f"http://{ip_local()}:5000"
qrcode.make(url).save(caminho_qrcode)
print("QR Code gerado para:", url)
print("Arquivo salvo em:", caminho_qrcode)