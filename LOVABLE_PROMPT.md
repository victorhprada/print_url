# 🎨 Prompt para Frontend no Lovable (Processamento em Lotes)

Cole este prompt completo no Lovable:

---

## PROMPT:

Crie uma aplicação web moderna para processar screenshots e PDFs de URLs usando **processamento em lotes**.

### CONTEXTO TÉCNICO:

O backend processa **até 20 URLs por vez** (cada lote leva ~2-3 minutos). O frontend deve:
1. Dividir todas as URLs em lotes de 20
2. Processar cada lote sequencialmente
3. Mostrar progresso total
4. Permitir download de cada lote ou todos combinados

### FUNCIONALIDADES:

**1. Upload de CSV**
- Drag-and-drop ou botão
- Validação: apenas .csv
- Preview: primeiras 5 URLs + total detectado
- Cálculo automático: "X lotes de 20 URLs" (ex: 164 URLs = 9 lotes)

**2. Painel de Configuração**
- Viewport: Largura (default: 1280) e Altura (default: 800)
- PDF: Formato (select: A4, Letter, etc - default A4) e Orientação (toggle: Retrato/Paisagem)
- Delimitador CSV (default: ";")

**3. Botão "Processar Tudo"**
- Inicia processamento sequencial dos lotes
- Mostra estimativa: "~18-27 minutos" (baseado em número de lotes)

**4. Progresso em Tempo Real** (CRÍTICO)

Dois níveis de progresso:

**A) Progresso Global:**
```
Processando lote 3 de 9
Progresso total: 60/164 URLs (36%)
Tempo decorrido: 6min 15s
Tempo estimado restante: ~12 minutos
```

**B) Progresso do Lote Atual:**
```
Lote 3: Processando...
20 URLs neste lote
[barra de progresso indeterminada enquanto processa]
```

**5. Resultados e Downloads**

Após processar cada lote:
```
✓ Lote 1: 20 URLs - 3min 12s [Baixar ZIP]
✓ Lote 2: 20 URLs - 2min 58s [Baixar ZIP]
⏳ Lote 3: Processando... (1min 45s)
⏸️ Lote 4: Aguardando...
```

Opções no final:
- **"Baixar Todos"** (combina ZIPs em um único arquivo)
- **"Baixar Lotes Individualmente"** (links para cada ZIP)
- **"Processar Novo Arquivo"** (reinicia)

**6. Gestão de Erros**
- Se um lote falhar: mostrar erro + opção "Tentar lote novamente"
- Se usuário fechar aba: mostrar aviso "Processamento será interrompido"
- Toast notifications para cada evento importante

### DESIGN:

**Estilo:**
- Moderno e clean (shadcn/ui)
- Gradiente azul/roxo (#3B82F6 → #8B5CF6)
- Cards com sombras suaves
- Animações de transição suaves

**Ícones (Lucide React):**
- Upload: UploadCloud
- Settings: Settings
- Processing: Loader2 (animado)
- Success: CheckCircle2
- Download: Download
- Error: AlertCircle
- Batch: Package

**Responsivo:**
- Mobile-first
- Funciona em celular, tablet e desktop

### INTEGRAÇÃO COM API:

**Variável de ambiente:**
```
VITE_API_URL=https://seu-backend.onrender.com
```

**Endpoints:**

**1. Preview do CSV:**
```typescript
POST ${API_URL}/api/process-csv-preview
FormData: {
  file: File,
  delimiter: string
}
Response: {
  total: number,
  preview: Array<{url: string, tipo?: string}>,
  batches_needed: number
}
```

**2. Processar Lote:**
```typescript
POST ${API_URL}/api/process-batch
FormData: {
  urls: string,  // URLs separadas por \n (max 20)
  batch_number: number,
  viewport_width: number,
  viewport_height: number,
  pdf_format: string,
  landscape: boolean
}
Response: ZIP file
Headers: {
  'X-Batch-Number': '3',
  'X-URLs-Processed': '20'
}
```

### FLUXO DE PROCESSAMENTO:

```typescript
// 1. Dividir URLs em lotes
const urls = [...]; // 164 URLs
const batches = chunk(urls, 20); // 9 lotes de 20 (último com 4)

// 2. Processar cada lote sequencialmente
const results = [];
for (let i = 0; i < batches.length; i++) {
  setBatchNumber(i + 1);
  setCurrentBatchStatus('processing');
  
  const formData = new FormData();
  formData.append('urls', batches[i].join('\n'));
  formData.append('batch_number', i);
  formData.append('viewport_width', config.width);
  formData.append('viewport_height', config.height);
  formData.append('pdf_format', config.pdfFormat);
  formData.append('landscape', config.landscape);
  
  try {
    const response = await axios.post(
      `${API_URL}/api/process-batch`,
      formData,
      {
        responseType: 'blob',
        onDownloadProgress: (e) => {
          // Mostrar progresso do download
        }
      }
    );
    
    results.push({
      batch: i + 1,
      blob: response.data,
      filename: `lote${i+1}.zip`
    });
    
    setCompletedBatches(prev => [...prev, i]);
    
  } catch (error) {
    setFailedBatches(prev => [...prev, {batch: i, error}]);
  }
}

// 3. Todos os lotes completos
setAllCompleted(true);
```

### COMPONENTES PRINCIPAIS:

```
src/
├── components/
│   ├── FileUpload.tsx          // Upload com preview
│   ├── ConfigPanel.tsx         // Configurações
│   ├── BatchProgressCard.tsx   // Progresso de um lote
│   ├── GlobalProgress.tsx      // Progresso total
│   ├── BatchResults.tsx        // Lista de resultados
│   └── DownloadButtons.tsx     // Botões de download
├── lib/
│   ├── api.ts                  // Funções de API
│   └── utils.ts                // Chunk, combine ZIPs
└── App.tsx
```

### ESTADOS DA APLICAÇÃO:

```typescript
type AppState = 
  | 'idle'           // Esperando upload
  | 'previewing'     // Mostrando preview do CSV
  | 'configuring'    // Usuário ajustando configs
  | 'processing'     // Processando lotes
  | 'completed'      // Todos completos
  | 'partial_error'; // Alguns lotes falharam

type BatchState = {
  number: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  urls: string[];
  result?: Blob;
  error?: string;
  duration?: number;
};
```

### EXTRAS (IMPORTANTE):

**1. Persistência Local:**
- Salvar progresso no LocalStorage
- Se usuário fechar aba e voltar, perguntar: "Retomar processamento?"

**2. Aviso antes de fechar:**
```typescript
useEffect(() => {
  if (isProcessing) {
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = 'Processamento em andamento será perdido';
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }
}, [isProcessing]);
```

**3. Download Combinado:**
- Usar JSZip para combinar múltiplos ZIPs em um
- Manter estrutura de pastas (plataforma/aplicativo)

**4. Estimativa de Tempo:**
- Baseado em média dos lotes anteriores
- Atualiza dinamicamente

### TECNOLOGIAS:

- React 18+ com TypeScript
- Tailwind CSS
- shadcn/ui components
- Axios para HTTP
- Lucide React icons
- JSZip (para combinar ZIPs)
- date-fns (para formatação de tempo)

### EXEMPLO DE CSV:

```csv
url,tipo
https://exemplo.com/dashboard,plataforma
https://app.exemplo.com,aplicativo
```

### IMPORTANTE:

- Interface DEVE ser responsiva
- Loading states em todas operações
- Error handling robusto
- Usuário DEVE poder baixar lotes individuais antes de terminar todos
- Progress bar DEVE ser preciso e atualizar em tempo real
- Código TypeScript bem tipado
- Componentes reutilizáveis

---

**Crie essa aplicação completa com todos os componentes e funcionalidades descritas!** 🚀
