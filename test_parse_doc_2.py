import unittest
import pandas as pd

# Assuming the class is in a file named document_processor.py
# from document_processor import DocumentProcessor

# For the sake of this example, I'm redefining the class here so the test is self-contained.
class DocumentProcessor:
    def atualizar_payload_documentos(self, payload_saida, df_documents):
        """
        - nomeTipoConteudo = df_documents['tipo_documento'] quando idArquivo coincidir
        - tipoConteudo = None em todos os documentos
        """
        
        # cria o mapa idArquivo -> tipo_documento
        # Using .get for safety if columns might be missing, or assume strict contract
        try:
            mapa_tipos = dict(zip(df_documents['idArquivo'], df_documents['tipo_documento']))
        except KeyError:
            # If the DF is empty or malformed, we might want to handle it or let it raise.
            # For this logic, if columns don't exist, it crashes. 
            # If the DF is empty but columns exist, zip yields nothing, which is fine.
            if df_documents.empty:
                 mapa_tipos = {}
            else:
                 raise

        for doc in payload_saida.get('documento', []):
            id_arquivo = doc.get('idArquivo')
            
            # se idArquivo existir no DataFrame, atualiza nomeTipoConteudo
            if id_arquivo in mapa_tipos:
                doc['nomeTipoConteudo'] = mapa_tipos[id_arquivo]
            
            # em todos os casos, zera tipoConteudo
            doc['tipoConteudo'] = None
            
        return payload_saida

class TestDocumentProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = DocumentProcessor()

    def test_update_payload_success_match(self):
        """
        Test if nomeTipoConteudo is updated correctly when IDs match
        and if tipoConteudo is set to None.
        """
        # Arrange
        payload = {
            'documento': [
                {'idArquivo': 101, 'nomeTipoConteudo': 'OldType', 'tipoConteudo': 'Base64String...'},
                {'idArquivo': 102, 'nomeTipoConteudo': 'OldType', 'tipoConteudo': 'Base64String...'}
            ]
        }
        
        data = {
            'idArquivo': [101, 102],
            'tipo_documento': ['Contract', 'Invoice']
        }
        df = pd.DataFrame(data)

        # Act
        result = self.processor.atualizar_payload_documentos(payload, df)

        # Assert
        docs = result['documento']
        
        # Doc 1 checks
        self.assertEqual(docs[0]['nomeTipoConteudo'], 'Contract')
        self.assertIsNone(docs[0]['tipoConteudo'])
        
        # Doc 2 checks
        self.assertEqual(docs[1]['nomeTipoConteudo'], 'Invoice')
        self.assertIsNone(docs[1]['tipoConteudo'])

    def test_partial_match_logic(self):
        """
        Test where only one document matches the DataFrame. 
        The non-matching document should NOT have its nomeTipoConteudo changed,
        but SHOULD have tipoConteudo set to None.
        """
        # Arrange
        payload = {
            'documento': [
                {'idArquivo': 101, 'nomeTipoConteudo': 'Original', 'tipoConteudo': 'Data'},
                {'idArquivo': 999, 'nomeTipoConteudo': 'KeepMe', 'tipoConteudo': 'Data'} # Not in DF
            ]
        }
        
        df = pd.DataFrame({'idArquivo': [101], 'tipo_documento': ['NewType']})

        # Act
        result = self.processor.atualizar_payload_documentos(payload, df)

        # Assert
        docs = result['documento']
        
        # Match found
        self.assertEqual(docs[0]['nomeTipoConteudo'], 'NewType')
        self.assertIsNone(docs[0]['tipoConteudo'])
        
        # No match found
        self.assertEqual(docs[1]['nomeTipoConteudo'], 'KeepMe') # Should remain unchanged
        self.assertIsNone(docs[1]['tipoConteudo']) # Should still be cleared

    def test_empty_dataframe(self):
        """
        Test behavior when DataFrame is empty. No types should be updated.
        """
        # Arrange
        payload = {
            'documento': [
                {'idArquivo': 101, 'nomeTipoConteudo': 'Original', 'tipoConteudo': 'Data'}
            ]
        }
        
        # Empty DF with correct columns
        df = pd.DataFrame(columns=['idArquivo', 'tipo_documento'])

        # Act
        result = self.processor.atualizar_payload_documentos(payload, df)

        # Assert
        self.assertEqual(result['documento'][0]['nomeTipoConteudo'], 'Original')
        self.assertIsNone(result['documento'][0]['tipoConteudo'])

    def test_empty_payload_list(self):
        """
        Test behavior when the document list in payload is empty.
        """
        # Arrange
        payload = {'documento': []}
        df = pd.DataFrame({'idArquivo': [1], 'tipo_documento': ['A']})

        # Act
        result = self.processor.atualizar_payload_documentos(payload, df)

        # Assert
        self.assertEqual(result['documento'], [])

    def test_missing_documento_key(self):
        """
        Test behavior when 'documento' key is missing from payload.
        Code uses .get('documento', []), so it should handle gracefully.
        """
        # Arrange
        payload = {'outra_coisa': 123}
        df = pd.DataFrame({'idArquivo': [1], 'tipo_documento': ['A']})

        # Act
        result = self.processor.atualizar_payload_documentos(payload, df)

        # Assert
        self.assertEqual(result, {'outra_coisa': 123})

    def test_document_missing_id(self):
        """
        Test a document entry that lacks the 'idArquivo' key.
        """
        # Arrange
        payload = {
            'documento': [
                {'other_field': 'value', 'tipoConteudo': 'Data'}
            ]
        }
        df = pd.DataFrame({'idArquivo': [1], 'tipo_documento': ['A']})

        # Act
        result = self.processor.atualizar_payload_documentos(payload, df)

        # Assert
        # Should execute without error, id_arquivo becomes None.
        # None is not in map (unless map has None), so name doesn't change.
        # tipoConteudo should be cleared.
        self.assertIsNone(result['documento'][0]['tipoConteudo'])

if __name__ == '__main__':
    unittest.main()
