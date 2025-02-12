from flask import Flask, request, jsonify, render_template
from requests.auth import HTTPBasicAuth
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from ldap3 import Server, Connection, ALL


app = Flask(__name__)
CORS(app)

# PENSANDO EM BOAS PRÁTICAS O VALOR DESSES PARÂMETROS DEVE SER ARMAZENADO EM UM ARQUIVO .ENV
LDAP_SERVER = ""  # Defina o endereço do seu servidor LDAP
LDAP_USER = ""    # Usuário LDAP com permissão para realizar a busca
LDAP_PASSWORD = "" # Senha do usuário LDAP


def validar_usuario_ldap(username, cpf, birthdate):
    conn = None  # Inicializa conn como None para garantir que a variável existe
    try:
        server = Server(LDAP_SERVER, get_info=ALL)
        conn = Connection(server, user=LDAP_USER, password=LDAP_PASSWORD, authentication='SIMPLE')
        if not conn.bind():
            return {"error": "Erro ao conectar ao servidor LDAP."}

        # Buscar o usuário no LDAP
        search_filter = f"(sAMAccountName={username})"
        conn.search('', search_filter, attributes=['', ''])  # Inserir a OU de busca e os atributos respectivos ao cpf e a data de nascimento

        if not conn.entries:
            return {"error": "Usuário não encontrado."}

        user_data = conn.entries[0]
        ldap_cpf = user_data.extensionAttribute10.value
        ldap_birthdate = user_data.extensionAttribute1.value

        # Verificar CPF e Data de Nascimento
        if ldap_cpf != cpf:
            return {"error": "CPF inválido para o usuário."}
        if ldap_birthdate != birthdate:
            return {"error": "Data de nascimento inválida."}

        return {"success": True}  # Usuário validado com sucesso

    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:  # Checa se conn não é None antes de tentar desvincular
            conn.unbind()

# Rota para servir o html
@app.route('/')
def index():
    return render_template('index.html')

#rota da API de conexão com SAP
@app.route('/trocarSenha', methods=['POST'])
def trocar_senha():
    data = request.get_json()
    system = data.get("system")
    username = data.get("network_user")
    cpf = data.get("cpf")
    birthdate = data.get("birthdate")

# recebeu todos os dados ? 
    if not system or not username or not cpf or not birthdate:
        return jsonify({"error": "Parâmetros 'system', 'uname', 'cpf' e 'birthdate' são obrigatórios"}), 400

# Validação via LDAP(AD)
    ldap_validation = validar_usuario_ldap(username, cpf, birthdate)
    if "error" in ldap_validation:
        return jsonify(ldap_validation), 400

    # Caso a validação no LDAP seja bem-sucedida, prossegue com a troca de senha no SAP

    # Parâmetros de conexão e autenticação, ARMAZENAR ESSES PARÂMETROS EM UM ARQUIVO .ENV
    url = ""
    username_auth = ""
    password_auth = ""

    #MUDAR ISSO AQUI 

    #cabeçalho da req SOAP, chamando a RFC Z criada no SAP
    soap_request = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:sap-com:document:sap:soap:functions:mc-style">
       <soapenv:Header/>
       <soapenv:Body>
          <urn:ZTrocarSenha>
             <ISystem>{system}</ISystem>
             <IUname>{username}</IUname>
          </urn:ZTrocarSenha>
       </soapenv:Body>
    </soapenv:Envelope>"""

    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
    }

    response = requests.post(url, data=soap_request, headers=headers, auth=HTTPBasicAuth(username_auth, password_auth), verify=False)

    # Tratativa de mensagens
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'xml')
        e_return = soup.find('EReturn')

        messages = []
        if e_return:
            items = e_return.find_all('item')
            for item in items:
                type_element = item.find('Type').text if item.find('Type') else ''
                message_element = item.find('Message').text if item.find('Message') else ''
                messages.append({"type": type_element, "message": message_element})
            return jsonify({"status": "success", "messages": messages})
        else:
            return jsonify({"status": "success", "messages": "Nenhuma mensagem encontrada na resposta."})
    else:
        return jsonify({"error": "Falha na requisição ao SAP", "status_code": response.status_code}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
