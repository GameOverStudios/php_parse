const fs = require("fs");
const path = require("path");
const engine = require("php-parser");

// Inicializa uma nova instância do parser
const parser = new engine({
  parser: {
    extractDoc: true,
    php7: true,
  },
  ast: {
    withPositions: true,
  },
});

// Função para garantir que o diretório de saída exista
function garantirDiretorioSaida() {
    const dir = path.join(__dirname, 'output');
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir);
        console.log('Diretório output criado.');
    }
    return dir;
}

// Função para verificar se o diretório deve ser ignorado
function deveIgnorarDiretorio(diretorio) {
    return /upgrade|xero|api|artificer|azure|cas_|charts|chat|datafox|decorous|dolphin|drupal|editor|elasticsearch|facebook|fontawesome|froala|google|intercom|linkedin|lucid|mailchip|nexus|oauth2|ocean|okta|opencv|plyr|profiler|protean|se_migration|shopify|smtpmailer|snipcart|stripe_connect|twitter|una_connect|xero|update/i.test(diretorio);
}

// Função para ler arquivos PHP e salvar a análise
function lerArquivosPhp(diretorio, outputDir) {
    const arquivos = fs.readdirSync(diretorio, { withFileTypes: true });

    arquivos.forEach(arquivo => {
        const caminhoArquivo = path.join(diretorio, arquivo.name);
        
        if (arquivo.isDirectory()) {
            // Ignora diretórios que contêm "upgrade" ou "update" no nome
            if (!deveIgnorarDiretorio(caminhoArquivo)) {
                // Chamada recursiva se for um diretório
                lerArquivosPhp(caminhoArquivo, outputDir);
            } else {
                console.log(`Ignorando diretório: ${caminhoArquivo}`);
            }
        } else if (arquivo.isFile() && arquivo.name.endsWith('.php')) {
            const conteudo = fs.readFileSync(caminhoArquivo, 'utf8');
            // Parse o conteúdo do arquivo
            const resultado = parser.parseCode(conteudo);
            const analise = JSON.stringify(resultado, null, 2);
            
            // Salva a análise em um arquivo
            const nomeArquivoSaida = path.join(outputDir, `${arquivo.name}.json`);
            fs.writeFileSync(nomeArquivoSaida, analise);
            console.log(`Análise de ${caminhoArquivo} salva em ${nomeArquivoSaida}`);
        }
    });
}

// Altere o caminho do diretório conforme necessário
diretorio = 'c:/xampp/htdocs/una/modules';
outputDir = garantirDiretorioSaida();
lerArquivosPhp(diretorio, outputDir);

diretorio = 'c:/xampp/htdocs/una/inc';
outputDir = garantirDiretorioSaida();
lerArquivosPhp(diretorio, outputDir);
