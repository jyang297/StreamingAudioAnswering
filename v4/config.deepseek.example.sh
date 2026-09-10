# Source this file in the same terminal where you run the PoC.
# Set DEEPSEEK_API_KEY locally; never put its value in this tracked file.
export RAG_LLM_BASE_URL='https://api.deepseek.com'
export RAG_LLM_MODEL='deepseek-v4-flash'
export RAG_LLM_API_KEY_ENV='DEEPSEEK_API_KEY'
export RAG_LLM_THINKING='disabled'
export RAG_DB_HOST='127.0.0.1'
export RAG_DB_PORT='55432'
export RAG_DB_NAME='rag_fixture'
export RAG_DB_USER='rag_reader'
