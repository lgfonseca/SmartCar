from flask import Flask, request, render_template, jsonify
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import pandas as pd
import webbrowser
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('formulario.html')

@app.route('/executar', methods=['POST'])
def executar():
    VIN = request.form.get('VIN')
    ODO = request.form.get('ODO')
    opcao_selecionada = float(request.form.get('opcao_selecionada'))

    try:
        
        chrome_driver_path = "./chromedriver"  # substitua pelo caminho correto
        servico = webdriver.Chrome(executable_path=chrome_driver_path)
        
        #servico = Service(ChromeDriverManager().install())
        navegador = webdriver.Chrome(service=servico)
        navegador.minimize_window()
        

        navegador.get("https://api.manheim.com/auth/authorization.oauth2?adaptor=manheim_customer&client_id=zdvy6trhqhe94qvmzpkq7v52&redirect_uri=https://mmr.manheim.com/oauth/callback&response_type=code&scope=profile+openid+email&signup=manheim&state=country%3DUS%26popup%3Dtrue%26source%3Dman")

        user = navegador.find_element(By.XPATH, '//*[@id="user_username"]')
        user.send_keys("Marciogomesvip")

        senha = navegador.find_element(By.XPATH, '//*[@id="user_password"]')
        senha.send_keys("MIXcds02@#")
        senha.send_keys(Keys.RETURN)

        InputVin = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="vinText"]')))
        InputVin.send_keys(VIN)
        InputVin.send_keys(Keys.RETURN)

        time.sleep(2)

        ODO = pd.to_numeric(ODO)
        Odometro = navegador.find_element(By.XPATH, '//input[@id="Odometer"]')
        Odometro.send_keys(str(ODO))
        Odometro.send_keys(Keys.RETURN)

        botao = {
            5.0: 2,
            4.5: 7,
            4.0: 12,
            3.5: 17,
            3.0: 22,
            2.5: 27,
            2.0: 32,
            1.5: 37,
            1.0: 42
        }.get(opcao_selecionada, 1)

        Combox = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="Condition Report"]/div[1]/div/div[1]/div/div[2]/div')))
        Combox.click()

        xpath = f'//*[@id="Condition Report"]/div[1]/div/div[1]/div/div[2]/div[2]/button[{botao}]/span'
        Grade = WebDriverWait(navegador, 10).until(EC.visibility_of_element_located((By.XPATH, xpath)))
        Grade.click()

        AdjustedMMR = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div[2]/div/div/div/div[2]/div[2]/div/div[1]/div[2]/div[2]/div/div/div[1]/div/div[2]/div[2]/div[1]')))
        TAdjustedMMR = AdjustedMMR.text

        MMRRange = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div[2]/div/div/div/div[2]/div[2]/div/div[1]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[2]/span/span[1]')))
        TMMRRange = MMRRange.text

        EstimatedRetailValue = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div[2]/div/div/div/div[2]/div[2]/div/div[4]/div[5]/div/div/div/div/div/div[1]')))
        TEstimatedRetailValue = EstimatedRetailValue.text

        TypicalRange1 = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div[2]/div/div/div/div[2]/div[2]/div/div[4]/div[5]/div/div/div/div/div/div[2]/div/div[2]/span[1]')))
        TTypicalRange1 = TypicalRange1.text

        TypicalRange2 = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div[2]/div/div/div/div[2]/div[2]/div/div[4]/div[5]/div/div/div/div/div/div[2]/div/div[2]/span[2]')))
        TTypicalRange2 = TypicalRange2.text

        ModelCarro = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div[2]/div/div/div/div[2]/div[1]/div/div[1]/h4')))
        ModelCarro = ModelCarro.text

        pasta_downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
        arquivos_downloads = os.listdir(pasta_downloads)
        arquivos_csv = [arquivo for arquivo in arquivos_downloads if arquivo.endswith('.csv')]

        if len(arquivos_csv) > 0:
            caminho_arquivo = os.path.join(pasta_downloads, max(arquivos_csv, key=lambda arquivo: os.path.getmtime(os.path.join(pasta_downloads, arquivo))))
            colunas_desejadas = ['Date', 'Price (USD)', 'Odometer (mi)', 'Condition', 'Year', 'Exterior Color']
            df = pd.read_csv(caminho_arquivo, usecols=colunas_desejadas)

            df['Odometer (mi)'] = df['Odometer (mi)'].str.replace(',', '').astype(float)
            df = df.rename(columns={'Condition': 'Grade'})

            df['Odometer (mi)'] = pd.to_numeric(df['Odometer (mi)'], errors='coerce')
            df['Grade'] = pd.to_numeric(df['Grade'], errors='coerce')
            df['Price (USD)'] = df['Price (USD)'].str.replace('$', '')
            df['Price (USD)'] = pd.to_numeric(df['Price (USD)'], errors='coerce')

            filtered_df = df[(df['Odometer (mi)'] >= ODO - 10000) & 
                             (df['Odometer (mi)'] <= ODO + 10000) & 
                             (df['Grade'] >= opcao_selecionada - 0.5) & 
                             (df['Grade'] <= opcao_selecionada + 0.5)]

            num_linhas_filtradas = filtered_df.shape[0]
            soma_price = filtered_df['Price (USD)'].sum()
            PrecoSugerido = soma_price / num_linhas_filtradas if num_linhas_filtradas > 0 else 0
        else:
            return jsonify({'error': 'Nenhum arquivo CSV encontrado no diretório de downloads.'}), 500

        navegador.quit()

        return render_template('resultado.html', 
            ModelCarro=ModelCarro,
            TAdjustedMMR=TAdjustedMMR,
            TMMRRange=TMMRRange,
            TEstimatedRetailValue=TEstimatedRetailValue,
            TTypicalRange1=TTypicalRange1,
            TTypicalRange2=TTypicalRange2,
            TAutoCheckScore="",  # Adicione valores conforme necessário
            TAutoCheckScoreComparation="",
            TMajorStateTitleBrandCheck="",
            TAcidenteCheck="",
            TDamageCheck="",
            Preco_Sugerido=PrecoSugerido,
            TValueGurus="",
            FilteredDataFrame=filtered_df.to_html(index=False))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000')

if __name__ == '__main__':
    threading.Timer(1, open_browser).start()
    app.run(debug=True)