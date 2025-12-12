## Contexto

Problema:
Ideia:
Escopo:
Talvez explicar um pouco porque precisa dessa peça e como que essa gestao de e-mails acontece hoje
E comentar que isso é um reuso da peça de RT Cross 
E talvez explicar qual que era a ideal total: categorizar e-mails + tipificacao + DI4

## Objetivo 
Responsável por fazer a **triagem de emails** na caixa de implantação de seguros saúde e **categorizá-los** conforme regras de negócio

* **Etapa 1 – Identificar Empresa:** Chamar agente para **extrair CNPJ** da empresa no título do e-mail 
* **Etapa 2 – Classificar Demanda:** Chamar agente para **classificar e-mail** com base no contexto do e-mail e regras de negócio

## Etapa 1 – Identificar Empresa 

**Objetivo**:
Resumir em um parágrafo o que tá no prompt 

**Inputs**:

* `prosta` (JSON): As informações da proposta    
* `kit_documentos` (str): O kit completo de todos os documentos necessários por operadora e porte.
