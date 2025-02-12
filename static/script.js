document.getElementById('submitBtn').addEventListener('click', function() {
    const system = document.getElementById('system').value;
    const network_user = document.getElementById('username').value.toUpperCase();
    let cpf = document.getElementById('cpf').value;

    // Recupera a data de nascimento e formata
    let birthdate = document.getElementById('birthdate').value.replace(/-/g, '');
    birthdate = birthdate.slice(6, 8) + birthdate.slice(4, 6) + birthdate.slice(0, 4);

    // Adiciona validação para garantir que o CPF contém apenas números
    if (!/^\d{11}$/.test(cpf)) {
        alert('Por favor, insira um CPF válido com 11 dígitos numéricos.');
        return;
    }

    if (!system || !network_user || !cpf || !birthdate) {
        alert('Por favor, preencha todos os campos.');
        return;
    }

    const data = {
        system: system,
        network_user: network_user,
        cpf: cpf,
        birthdate: birthdate
    };

    const popup = document.getElementById('popup');
    const popupMessage = document.getElementById('popupMessage');
    const loader = document.getElementById('loader');
    popup.style.display = 'flex';
    popupMessage.innerHTML = "Aguardando resposta...";
    loader.style.display = 'block';

    fetch('http://localhost:5000/trocarSenha', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        loader.style.display = 'none';
        if (Array.isArray(data.messages) && data.messages.length > 0) {
            // Junta todas as mensagens em uma única string, separando-as por quebras de linha
            const combinedMessages = data.messages.map(msg => `${msg.message}`).join('<br>');
            popupMessage.innerHTML = combinedMessages;
        } else {
            popupMessage.innerHTML = 'Erro: ' + data.error;
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        loader.style.display = 'none';
        popupMessage.innerHTML = 'Erro ao validar dados do usuário';
    })
    .finally(() => {

        clearFields();
    });
});

function clearFields() {
    document.getElementById('system').value = '';
    document.getElementById('username').value = '';
    document.getElementById('cpf').value = '';
    document.getElementById('birthdate').value = '';
}

document.getElementById('closePopupBtn').addEventListener('click', function() {
    document.getElementById('popup').style.display = 'none';
});
