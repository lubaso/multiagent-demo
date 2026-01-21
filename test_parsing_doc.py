import pytest
import pandas as pd

# --- The Class Under Test ---
class DocumentProcessor:
    def atualizar_payload_documentos(self, payload_saida, df_documents):
        """
        - nomeTipoConteudo = df_documents['tipo_documento'] when idArquivo matches
        - tipoConteudo = None in all documents
        """
        
        # Create map idArquivo -> tipo_documento
        # Handle empty DF safely
        if df_documents.empty:
            mapa_tipos = {}
        else:
            mapa_tipos = dict(zip(df_documents['idArquivo'], df_documents['tipo_documento']))
        
        for doc in payload_saida.get('documento', []):
            id_arquivo = doc.get('idArquivo')
            
            # Update nomeTipoConteudo if match found
            if id_arquivo in mapa_tipos:
                doc['nomeTipoConteudo'] = mapa_tipos[id_arquivo]
            
            # Always clear tipoConteudo
            doc['tipoConteudo'] = None
            
        return payload_saida

# --- Pytest Fixtures ---

@pytest.fixture
def processor():
    return DocumentProcessor()

@pytest.fixture
def sample_df():
    data = {
        'idArquivo': [101, 102, 103],
        'tipo_documento': ['Contract', 'Invoice', 'Receipt']
    }
    return pd.DataFrame(data)

@pytest.fixture
def base_payload():
    return {
        'documento': [
            {'idArquivo': 101, 'nomeTipoConteudo': 'OldType', 'tipoConteudo': 'Base64Data'},
            {'idArquivo': 999, 'nomeTipoConteudo': 'KeepMe', 'tipoConteudo': 'Base64Data'}
        ]
    }

# --- Test Cases ---

def test_update_payload_match_found(processor, sample_df, base_payload):
    """
    Scenario: ID 101 exists in DF. 
    Expectation: nomeTipoConteudo updates to 'Contract', tipoConteudo becomes None.
    """
    result = processor.atualizar_payload_documentos(base_payload, sample_df)
    doc_101 = result['documento'][0]

    assert doc_101['nomeTipoConteudo'] == 'Contract'
    assert doc_101['tipoConteudo'] is None

def test_update_payload_no_match(processor, sample_df, base_payload):
    """
    Scenario: ID 999 does NOT exist in DF.
    Expectation: nomeTipoConteudo remains 'KeepMe', but tipoConteudo is cleared.
    """
    result = processor.atualizar_payload_documentos(base_payload, sample_df)
    doc_999 = result['documento'][1]

    assert doc_999['nomeTipoConteudo'] == 'KeepMe' # Should not change
    assert doc_999['tipoConteudo'] is None         # Should still be cleared

def test_empty_dataframe(processor):
    """
    Scenario: DataFrame is empty.
    Expectation: No names change, all contents cleared.
    """
    df_empty = pd.DataFrame(columns=['idArquivo', 'tipo_documento'])
    payload = {
        'documento': [{'idArquivo': 101, 'nomeTipoConteudo': 'Original', 'tipoConteudo': 'Data'}]
    }

    result = processor.atualizar_payload_documentos(payload, df_empty)
    
    assert result['documento'][0]['nomeTipoConteudo'] == 'Original'
    assert result['documento'][0]['tipoConteudo'] is None

def test_empty_payload_list(processor, sample_df):
    """
    Scenario: Payload 'documento' list is empty.
    Expectation: Returns empty list structure without error.
    """
    payload = {'documento': []}
    result = processor.atualizar_payload_documentos(payload, sample_df)
    
    assert result['documento'] == []

def test_missing_document_key(processor, sample_df):
    """
    Scenario: Payload missing 'documento' key entirely.
    Expectation: Returns payload as is (handled by .get default).
    """
    payload = {'meta': 'data'}
    result = processor.atualizar_payload_documentos(payload, sample_df)
    
    assert result == {'meta': 'data'}

def test_document_missing_id(processor, sample_df):
    """
    Scenario: A document in the list is missing the 'idArquivo' key.
    Expectation: Skips update logic, clears content, no error raised.
    """
    payload = {
        'documento': [{'nomeTipoConteudo': 'Test', 'tipoConteudo': 'Data'}]
    }
    
    result = processor.atualizar_payload_documentos(payload, sample_df)
    doc = result['documento'][0]
    
    assert doc['nomeTipoConteudo'] == 'Test' # Unchanged
    assert doc['tipoConteudo'] is None       # Cleared
