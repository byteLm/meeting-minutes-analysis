import requests
import re
import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from datetime import datetime
from typing import Optional

class LocalLLMClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen3:8b"):
        self.base_url = base_url
        self.model = model
        self.timeout = 60
    
    def extract_date(self, text_snippet: str) -> Optional[str]:
        """
        Usa LLM local para extrair data do texto
        """
        prompt = f"""
        ANALISE ESTE TEXTO DE ATA E EXTRAIA APENAS A DATA MENCIONADA.
        
        TEXTO: "{text_snippet}"
        
        INSTRUÇÕES:
        1. Identifique a data mencionada no texto
        2. Retorne APENAS no formato JSON: {{"data": "YYYY-MM-DD"}}
        3. Se não encontrar data clara, retorne {{"data": null}}
        4. Use números para meses (01-12)
        5. Ignore datas de outros contextos, foque na data da reunião
        
        Exemplos corretos:
        - "12 de março de 2023" → "2023-03-12"
        - "15/04/2021" → "2021-04-15"
        - "3 de outubro de 2020" → "2020-10-03"
        
        Não responda NENHUM TEXTO além do JSON solicitado.
        """
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "num_predict": 5000 
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result['response'].strip()
                
                # Limpar resposta removendo caracteres problemáticos
                response_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', response_text)
                
                # Extrair JSON da resposta
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    try:
                        result_json = json.loads(json_match.group(0))
                        date_value = result_json.get('data')
                        
                        if date_value and date_value != 'null':
                            # Tentar parsear a data em múltiplos formatos
                            try:
                                dt = datetime.strptime(date_value, "%Y-%m-%d")
                                return dt.strftime("%Y-%m-%d")
                            except ValueError:
                                # Tentar outros formatos comuns
                                for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%d de %B de %Y", "%d de %b de %Y"]:
                                    try:
                                        dt = datetime.strptime(date_value, fmt)
                                        return dt.strftime("%Y-%m-%d")
                                    except ValueError:
                                        continue
                    except json.JSONDecodeError:
                        pass
                
                # Fallback: procurar padrão de data na resposta
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', response_text)
                if date_match:
                    try:
                        dt = datetime.strptime(date_match.group(0), "%Y-%m-%d")
                        return dt.strftime("%Y-%m-%d")
                    except ValueError:
                        pass
                
            return None
            
        except requests.exceptions.RequestException:
            print("Ollama não está rodando. Inicie com: ollama serve")
            return None
        except Exception as e:
            print(f"Erro na LLM local: {e}")
            return None

