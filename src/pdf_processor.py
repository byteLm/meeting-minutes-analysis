import os
import sys
import re
from datetime import datetime
from typing import Dict, Optional
import pandas as pd
import pdfplumber

sys.path.append(os.path.abspath(os.path.join(os.getcwd())))
sys.path.append(os.path.dirname(__file__))

from llm_client import LocalLLMClient


class PDFProcessor:
    def __init__(self, directory_path: str, use_llm: bool = True):
        self.directory_path = directory_path
        self.cbh_mapping = {
            'LN': 'Litoral Norte',
            'LS': 'Litoral Sul', 
            'PB': 'Rio Paraíba',
            'PA': 'Piranhas'
        }

        self.llm_client = LocalLLMClient() if use_llm else None

        # Dicionários de conversão baseados no código R
        self.conv_dias_vinte = {
            "dezesseis dias ": "16-", "dezessete dias ": "17-", "dezoito dias ": "18-", 
            "dezenove dias ": "19-", "vinte dias ": "20-", "vinte e um dias ": "21-", 
            "vinte um dias": "21-", "vinte e dois dias ": "22-", 
            "vinte e três dias ": "23-", "vinte três dias ": "23-",
            "vinte e quatro dias ": "24-", "vinte quatro dias ": "24-",
            "vinte e cinco dias ": "25-", "vinte cinco ": "25-",
            "vinte e seis dias ": "26-", "vinte e sete dias ": "27-", 
            "vinte sete": "27-", "vinte e oito dias ": "28-", 
            "vinte e nove dias ": "29-", "trinta dias ": "30-",
            "trinta e um dias ": "31-"
        }

        self.conv_dias = {
            "um dias ": "1-", "primeiro dia ": "1-", "dois dias ": "2-", "três dias ": "3-", 
            "quatro dias ": "4-", "cinco dias ": "5-", "seis dias ": "6-", "sete dias ": "7-", 
            "oito dias ": "8-", "nove dias ": "9-", "dez dias ": "10-", "onze dias ": "11-", 
            "doze dias ": "12-", "treze dias ": "13-", "quatorze dias ": "14-", 
            "quartoze dias ": "14-", "catorze dias ": "14-", "Catorze dias ": "14-",
            "quinze dias ": "15-", "trinta dias ": "30-"
        }

        self.conv_meses = {
            "do mês de janeiro ": "01-", "do mês de fevereiro ": "02-", "do mês de março": "03-",
            "do mês de abril ": "04-", "do mês de maio ": "05-", "do mês de junho ": "06-",
            "do mês de julho ": "07-", "do mês de agosto ": "08-", "do mês de setembro ": "09-",
            "do mês de outubro ": "10-", "do mês de novembro ": "11-", "do mês de dezembro ": "12-"
        }

        self.conv_anos_especiais = {
            "do ano dois mil e dez": "2010", "do ano de dois mil e ": "20", "do ano de 2021": "2021",
            "do ano de 2020": "2020", "do ano dois mil e ": "20"
        }

        self.conv_anos_milhar_final = {
            "de dois mil e ": "20"
        }

        self.conv_anos_dezena = {
            "onze": "11", "doze": "12", "treze": "13", "quatorze": "14", "catorze": "14", 
            "quinze": "15", "dezesseis": "16", "dezessete": "17", "dezoito": "18", 
            "dezenove": "19", "vinte um": "21", "vinte e um": "21", "vinte dois": "22", 
            "vinte e dois": "22"
        }

        self.conv_anos_final = {
            "vinte": "20", "um": "01", "dois": "02", "três": "03", "quatro": "04", 
            "cinco": "05", "seis": "06", "sete": "07", "oito": "08", "nove": "09", "dez": "10"
        }
    
    def read_pdf(self, file_path: str) -> str:
        """
        Extrai texto de um arquivo PDF
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text.strip()
        except Exception as e:
            print(f"Erro ao ler o arquivo {file_path}: {e}")
            return ""
    
    def extract_metadata_from_filename(self, filename: str) -> Dict:
        """
        Extrai metadados do nome do arquivo
        """
        pattern = r'Ata_CBH_([A-Z]{2})_(\d{4})_(\d{2})_([A-Za-z]+)\.pdf'
        match = re.match(pattern, filename)
        
        if match:
            cbh_code, year, month, meeting_type = match.groups()
            return {
                'cbh_code': cbh_code,
                'year': year,
                'month': month,
                'tipo': meeting_type.lower()
            }
        return {}
    
    def extract_date_from_text(self, text: str, filename: str) -> Optional[str]:
        """
        Extrai a data do corpo do texto da ata com múltiplas estratégias
        """
        # Primeiro tenta padrões regex tradicionais
        date_patterns = [
            r'(\d{1,2})\s*de\s*([a-zç]+)\s*de\s*(\d{4})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{1,2})-(\d{1,2})-(\d{4})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'dia\s*(\d{1,2})\s*de\s*([a-zç]+)\s*de\s*(\d{4})'
        ]
        
        month_mapping = {
            'janeiro': '01', 'fevereiro': '02', 'março': '03', 'marco': '03',
            'abril': '04', 'maio': '05', 'junho': '06', 'julho': '07',
            'agosto': '08', 'setembro': '09', 'outubro': '10',
            'novembro': '11', 'dezembro': '12'
        }
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text.lower()[:2000])
            for match in matches:
                if len(match) == 3:
                    day, month_str, year = match
                    
                    # Converter mês por extenso para número
                    if month_str in month_mapping:
                        month_num = month_mapping[month_str]
                    else:
                        month_num = month_str.zfill(2)
                    
                    day = day.zfill(2)
                    
                    # Validar data
                    try:
                        dt = datetime.strptime(f"{year}-{month_num}-{day}", "%Y-%m-%d")
                        return dt.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
        
        # Se regex tradicional falhar, tenta o método do código R
        r_style_date = self.extract_date_r_style(text)
        if r_style_date:
            return r_style_date
        
        # Se tudo falhar, usa LLM
        if self.llm_client:
            print(f"Usando LLM para extrair data de {filename}...")
            words = text.split()
            text_snippet = " ".join(words[:500])  # Aumentado contexto
            
            llm_date = self.llm_client.extract_date(text_snippet)
            if llm_date:
                try:
                    dt = datetime.strptime(llm_date, "%Y-%m-%d")
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    print(f"Data da LLM inválida: {llm_date}")
        
        return None
    
    def extract_date_r_style(self, text: str) -> Optional[str]:
        """
        Extrai datas usando o método do código R
        """
        try:
            # Padrão para encontrar a string de data no formato "Aos ... ,"
            pattern = r'Aos\s*(.*?)\s*,'
            match = re.search(pattern, text, re.IGNORECASE)
            
            if not match:
                # Tenta padrão alternativo
                pattern = r'Ao\s*(.*?)\s*,'
                match = re.search(pattern, text, re.IGNORECASE)
            
            if match:
                date_str = match.group(1).lower()
                
                # Aplica as conversões do código R
                for old, new in self.conv_dias_vinte.items():
                    date_str = date_str.replace(old, new)
                
                for old, new in self.conv_dias.items():
                    date_str = date_str.replace(old, new)
                
                for old, new in self.conv_meses.items():
                    date_str = date_str.replace(old, new)
                
                for old, new in self.conv_anos_especiais.items():
                    date_str = date_str.replace(old, new)
                
                for old, new in self.conv_anos_milhar_final.items():
                    date_str = date_str.replace(old, new)
                
                for old, new in self.conv_anos_dezena.items():
                    date_str = date_str.replace(old, new)
                
                for old, new in self.conv_anos_final.items():
                    date_str = date_str.replace(old, new)
                
                # Tenta extrair data no formato final (DD-MM-YYYY)
                date_match = re.search(r'(\d{1,2})-(\d{1,2})-(\d{4})', date_str)
                if date_match:
                    day, month, year = date_match.groups()
                    try:
                        dt = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
                        return dt.strftime("%Y-%m-%d")
                    except ValueError:
                        pass
                
                # Tenta outros padrões
                date_match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
                if date_match:
                    year, month, day = date_match.groups()
                    try:
                        dt = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
                        return dt.strftime("%Y-%m-%d")
                    except ValueError:
                        pass
            
            return None
        except Exception as e:
            print(f"Erro no método R-style: {e}")
            return None
    
    def process_single_file(self, filename: str) -> Optional[Dict]:
        """
        Processa um único arquivo PDF
        """
        if not filename.lower().endswith('.pdf'):
            return None
        
        file_path = os.path.join(self.directory_path, filename)
        
        # Extrair metadados do nome do arquivo
        metadata = self.extract_metadata_from_filename(filename)
        if not metadata:
            print(f"Formato de nome inválido: {filename}")
            return None
        
        # Ler texto do PDF
        text = self.read_pdf(file_path)
        if not text:
            print(f"Texto vazio ou erro na leitura: {filename}")
            return None
        
        # Extrair data do texto
        extracted_date = self.extract_date_from_text(text, filename)
        
        return {
            'ID': filename,
            'Data': extracted_date,
            'CBH': self.cbh_mapping.get(metadata['cbh_code'], metadata['cbh_code']),
            'Tipo': metadata['tipo'],
            'Texto': text
        }
    
    def process_all_files(self) -> pd.DataFrame:
        """
        Processa todos os arquivos PDF no diretório
        """
        files_data = []
        
        pdf_files = [f for f in os.listdir(self.directory_path) 
                    if f.lower().endswith('.pdf') and f.startswith('Ata_CBH')]
        
        print(f"Encontrados {len(pdf_files)} arquivos PDF para processar...")
        
        for filename in pdf_files:
            print(f"Processando: {filename}")
            file_data = self.process_single_file(filename)
            if file_data:
                files_data.append(file_data)
        
        # Criar DataFrame
        df = pd.DataFrame(files_data)
        
        # Converter e validar datas
        if not df.empty and 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce', format='%Y-%m-%d')
            df = df.sort_values('Data')
        
        return df

    def debug_dates(self, df: pd.DataFrame):
        """
        Função para debug das datas
        """
        print("\n=== DEBUG DE DATAS ===")
        print(f"Total de registros: {len(df)}")
        print(f"Datas nulas: {df['Data'].isna().sum()}")
        
        # Mostrar registros com datas problemáticas
        problem_dates = df[df['Data'].isna()]
        if not problem_dates.empty:
            print("\nArquivos com problemas de data:")
            for _, row in problem_dates.iterrows():
                print(f"- {row['ID']}: {row['Data']}")
        
        # Estatísticas de datas válidas
        valid_dates = df[df['Data'].notna()]
        if not valid_dates.empty:
            print(f"\nDatas válidas: {len(valid_dates)}")
            print(f"Período: {valid_dates['Data'].min()} até {valid_dates['Data'].max()}")
        
        return df

