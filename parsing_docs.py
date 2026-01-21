import pandas as pd

class DocumentProcessor:
    def atualizar_payload_documentos(self, payload_saida, df_documents):
        """
        - nomeTipoConteudo = df_documents['tipo_documento'] quando idArquivo coincidir
        - tipoConteudo = None em todos os documentos
        """
        
        # cria o mapa idArquivo -> tipo_documento
        mapa_tipos = dict(zip(df_documents['idArquivo'], df_documents['tipo_documento']))
        
        for doc in payload_saida.get('documento', []):
            id_arquivo = doc.get('idArquivo')
            
            # se idArquivo existir no DataFrame, atualiza nomeTipoConteudo
            if id_arquivo in mapa_tipos:
                doc['nomeTipoConteudo'] = mapa_tipos[id_arquivo]
            
            # em todos os casos, zera tipoConteudo
            doc['tipoConteudo'] = None
            
        return payload_saida
