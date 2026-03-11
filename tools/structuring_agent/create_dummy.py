from PIL import Image, ImageDraw
import os

def create_dummy_data():
    os.makedirs('dummy_data', exist_ok=True)
    
    # 1. Imagem Fake de Receita
    img = Image.new('RGB', (800, 1000), color='white')
    d = ImageDraw.Draw(img)
    text = """
    Dr. Jose Silva - CRM 12345
    Clinica Vida
    
    RECEITUARIO
    
    Paciente: Maria Teste da Silva
    CPF: 123.456.789-00
    Data: 28/01/2026
    
    Uso Oral
    1. Cannabidiol 5% ..................... 1 frasco
       Tomar 5 gotas a noite.
       
    Ass: Dr Jose
    """
    d.text((50, 50), text, fill=(0, 0, 0))
    img.save('dummy_data/receita_fake.jpg')
    
    # 2. Imagem Fake de RG (Simples)
    img_rg = Image.new('RGB', (600, 400), color='#ddd')
    d_rg = ImageDraw.Draw(img_rg)
    text_rg = """
    REPUBLICA FEDERATIVA DO BRASIL
    REGISTRO GERAL
    
    Nome: JOAO TESTE
    Nascimento: 01/01/1980
    CPF: 987.654.321-99
    """
    d_rg.text((20, 20), text_rg, fill=(0, 0, 0))
    img_rg.save('dummy_data/rg_fake.png')
    
    print("Dummy data gerado em dummy_data/")

if __name__ == "__main__":
    create_dummy_data()
