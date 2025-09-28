// Script para debug do frontend - cole no console do navegador

console.log("=== DEBUG FRONTEND - GRÁFICO DE DOSAGENS ===");

// 1. Verificar se o usuário está logado
const token = localStorage.getItem('token');
const user = localStorage.getItem('user');

console.log("1. Status de autenticação:");
console.log("Token existe:", !!token);
console.log("User existe:", !!user);

if (token) {
    console.log("Token (primeiros 50 chars):", token.substring(0, 50) + "...");
}

if (user) {
    try {
        const userData = JSON.parse(user);
        console.log("Dados do usuário:", userData);
    } catch (e) {
        console.log("Erro ao parsear dados do usuário:", e);
    }
}

// 2. Verificar se estamos na página correta
console.log("\n2. Informações da página:");
console.log("URL atual:", window.location.href);
console.log("Pathname:", window.location.pathname);

// 3. Verificar se os componentes de gráfico existem no DOM
console.log("\n3. Componentes no DOM:");
const dosageCharts = document.querySelectorAll('[class*="dosage"], [class*="Dosage"]');
console.log("Elementos com 'dosage' no className:", dosageCharts.length);

dosageCharts.forEach((el, index) => {
    console.log(`Elemento ${index + 1}:`, el.className, el);
});

// 4. Verificar se há erros React no console
console.log("\n4. Para verificar erros React, procure por:");
console.log("- Mensagens de erro em vermelho no console");
console.log("- Warnings sobre props não definidas");
console.log("- Erros de 'Cannot read property of undefined'");

// 5. Testar requisição manual
console.log("\n5. Testando requisição manual...");

if (token) {
    fetch('http://localhost:5002/api/dosagens/grafico/paciente/1?periodo=integral', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        console.log("Status da requisição manual:", response.status);
        return response.json();
    })
    .then(data => {
        console.log("Dados recebidos:", data);
        if (data.dados_grafico) {
            console.log("Pontos no gráfico:", data.dados_grafico.length);
        }
    })
    .catch(error => {
        console.error("Erro na requisição manual:", error);
    });
} else {
    console.log("Não é possível testar requisição - token não encontrado");
}

console.log("\n=== FIM DO DEBUG ===");
