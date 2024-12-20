import os
import pandas as pd
import requests


class WebScraper:
    def __init__(self, start_year, end_year, data_dir, base_dir, base_url):
        self.start_year = start_year
        self.end_year = end_year
        self.data_dir = data_dir
        self.base_dir = base_dir
        self.base_url = base_url
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(base_dir, exist_ok=True)

    def download_data(self):
        for year in range(self.start_year, self.end_year):
            for month in range(1, 13):
                url = self.base_url.format(year=year, month=month)
                year_dir = os.path.join(self.data_dir, str(year))
                os.makedirs(year_dir, exist_ok=True)

                file_name = f"execucao_exercicio_{year}_{month:02d}.csv"
                file_path = os.path.join(year_dir, file_name)

                if os.path.exists(file_path):
                    print(f"Arquivo {file_name} já existe. Pulando download.")
                    continue

                try:
                    response = requests.get(url, timeout=10)
                    if (
                        response.status_code == 200
                        and "text/csv" in response.headers.get("Content-Type", "")
                    ):
                        with open(file_path, "wb") as f:
                            f.write(response.content)
                        print(f"Arquivo salvo: {file_name}")
                    else:
                        print(
                            f"Sem dados disponíveis para {year}-{month:02d}. Encerrando o loop de anos."
                        )
                        break
                except requests.RequestException as e:
                    print(f"Erro ao processar {year}-{month:02d}: {e}")
                    continue

            else:
                continue
            break
        print("Processo de download de receitas concluído.")

    def download_static_files(self):
        files_to_download = {
            "unidade_gestora_pb": "https://dados.pb.gov.br:443/getcsv?nome=unidade_gestora_dadospb&exercicio={year}",
            "fonte_recurso_pb": "https://dados.pb.gov.br:443/getcsv?nome=fonte_recurso&exercicio={year}",
        }
        for year in range(self.start_year, self.end_year):
            year_dir = os.path.join(self.data_dir, str(year))
            os.makedirs(year_dir, exist_ok=True)

            for file_prefix, url_template in files_to_download.items():
                file_name = f"{file_prefix}_{year}.csv"
                file_path = os.path.join(year_dir, file_name)

                if os.path.exists(file_path):
                    print(f"Arquivo {file_name} já existe. Pulando download.")
                    continue

                try:
                    url = url_template.format(year=year)
                    response = requests.get(url, timeout=10)
                    if (
                        response.status_code == 200
                        and "text/csv" in response.headers.get("Content-Type", "")
                    ):
                        with open(file_path, "wb") as f:
                            f.write(response.content)
                        print(f"Arquivo salvo: {file_name}")
                    else:
                        print(f"Dados não disponíveis para o ano {year} - {file_name}.")
                except requests.RequestException as e:
                    print(
                        f"Erro ao baixar o arquivo {file_name} para o ano {year}: {e}"
                    )

        print("Processo de download dos arquivos estáticos concluído.")


def process_csv_files(data_dir, base_dir):
    receitas_files = []
    for year in os.listdir(data_dir):
        year_path = os.path.join(data_dir, year)
        if os.path.isdir(year_path):
            receitas_files.extend(
                [
                    os.path.join(year_path, file)
                    for file in os.listdir(year_path)
                    if file.startswith("execucao_exercicio") and file.endswith(".csv")
                ]
            )

    process_and_save(receitas_files, os.path.join(base_dir, "receita_pb.csv"))

    for prefix in ["unidade_gestora_pb", "fonte_recurso_pb"]:
        static_files = []
        for year in os.listdir(data_dir):
            year_path = os.path.join(data_dir, year)
            if os.path.isdir(year_path):
                static_files.extend(
                    [
                        os.path.join(year_path, file)
                        for file in os.listdir(year_path)
                        if file.startswith(prefix) and file.endswith(".csv")
                    ]
                )
        process_and_save(static_files, os.path.join(base_dir, f"{prefix}_final.csv"))


def process_and_save(files, output_path):
    dataframes = []
    for file in files:
        try:
            df = pd.read_csv(file, encoding="latin1", sep=";")
            dataframes.append(df)
            print(f"Arquivo {file} lido com sucesso.")
        except pd.errors.EmptyDataError:
            print(f"Arquivo {file} está vazio ou mal formatado.")
        except Exception as e:
            print(f"Erro ao processar o arquivo {file}: {e}")

    if dataframes:
        final_df = pd.concat(dataframes, ignore_index=True)
        final_df.to_csv(output_path, index=False)
        print(f"Arquivo final gerado com sucesso: {output_path}")
    else:
        print(f"Nenhum dado válido foi encontrado para {output_path}.")


def get_user_input():
    while True:
        try:
            start_year = int(input("Digite o ano de início (ex: 2024): "))
            end_year = int(input("Digite o ano de término (ex: 2025): "))
            if start_year >= end_year:
                print(
                    "O ano de início deve ser menor que o ano de término. Tente novamente."
                )
                continue
            return start_year, end_year
        except ValueError:
            print(
                "Por favor, insira um valor válido para o ano (número inteiro). Tente novamente."
            )


def main():
    start_year, end_year = get_user_input()

    base_dir = "./data"
    data_dir = os.path.join(base_dir, "webscraping")
    base_url = "https://dados.pb.gov.br/getcsv?nome=receitas_execucao&exercicio={year}&mes={month}"

    print(
        f"Iniciando o processo de web scraping para os anos {start_year} até {end_year - 1}."
    )

    scraper = WebScraper(start_year, end_year, data_dir, base_dir, base_url)
    scraper.download_data()
    scraper.download_static_files()

    process_csv_files(data_dir, base_dir)


if __name__ == "__main__":
    main()
