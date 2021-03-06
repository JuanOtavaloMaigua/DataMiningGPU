# -*- coding: utf-8 -*-
"""cuDForgProject.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1CLKfAStXWS21NTHuEbzSQtv6F7Q1RCFK

**- Analisis de palabras mas utilizadas por diversos candidatos**

-- Uso de cuDF

-- Uso de GPU

-- Librerias de cuda para procesamiento de datos tipo String

-- Demostar el bajo rendimiento de tiempo

-----------------------------------

Analisis de los tweets generados por candidatos y simpatizantes de las dignidades postuladas como son: Alcadia y Concejo de Particiapación Ciudadana. En el periodo de febrero y marzo para las elecciones del 2019 en el Ecuador.
"""

#Codigo para importar cudf
#https://medium.com/rapids-ai/run-rapids-on-google-colab-for-free-1617ac6323a8
#https://colab.research.google.com/drive/1rY7Ln6rEE1pOlfSHCYOVaqt8OvDO35J0#forceEdit=true&sandboxMode=true&scrollTo=m0jdXBRiDSzj
# Install RAPIDS
!git clone https://github.com/rapidsai/rapidsai-csp-utils.git
!bash rapidsai-csp-utils/colab/rapids-colab.sh stable

import sys, os

dist_package_index = sys.path.index('/usr/local/lib/python3.6/dist-packages')
sys.path = sys.path[:dist_package_index] + ['/usr/local/lib/python3.6/site-packages'] + sys.path[dist_package_index:]
sys.path
exec(open('rapidsai-csp-utils/colab/update_modules.py').read(), globals())

#codigo de prueba
import nvstrings, nvtext, cudf, numpy, nltk
s = nvstrings.to_device(["this is me","theme music",""])
t = nvstrings.to_device(['is','me'])
r = nvtext.replace_tokens(s,t,'_')
print(r)

from google.colab import drive 
drive.mount('/content/gdrive')

# Commented out IPython magic to ensure Python compatibility.
# Commented out IPython magic to ensure Python compatibility.
#/content/Gutenberg.zip

def get_txt_lines(data_dir):
    """
        Read text lines from gutenberg tests
        returns (text_ls,fname_ls) where 
        text_ls = input_text_lines and fname_ls = list of file names
    """
    text_ls = []
    fname_ls = []
    for fn in os.listdir(data_dir):
        full_fn = os.path.join(data_dir,fn)
        with open(full_fn,encoding="utf-8",errors="ignore") as f:
            content = f.readlines()
            text_ls += content
            ### dont add .txt to the file
            fname_ls += [fn[:-4]]*len(content)
    
    return text_ls, fname_ls    
    
print("File Read Time:")
# %time txt_ls,fname_ls = get_txt_lines('/content/gdrive/My Drive/GoogleColabProjects/cuDFProject/DataAspirantes')
df = cudf.DataFrame()

print("\nCUDF  Creation Time:")
# %time df['text'] = nvstrings.to_device(txt_ls)

df['label'] = nvstrings.to_device(fname_ls)
title_label_df = df['label'].str.split('-')
df['author'] = title_label_df[0]

df['type'] = title_label_df[1]
df = df.drop(labels=['label'])

df.head(10).to_pandas()

# remover caracteres especificos 
# ojo con la enie en el caso para espanol
filters = [ '!', '"', '#', '$', '%', '&', '(', ')', '*', '+', '-', '.', '/',  '\\', ':', ';', '<', '=', '>',
           '?', '@', '[', ']', '^', '_', '`', '{', '|', '}', '\~', '\t','\\n',"'",",",'~' , '—','1','2','3','4','5','6','7','8','9','0']

text_col_sample = df.head(5)
text_col_sample['text'].to_pandas()

text_col_sample['text_clean'] = text_col_sample['text'].str.replace_multi(filters, ' ', regex=False)
text_col_sample['text_clean'] = text_col_sample['text_clean'].str.lower()
text_col_sample['text_clean'].to_pandas()

nltk.download('stopwords') #para descargar las stopwords, siempre se debe descargar
STOPWORDS = nltk.corpus.stopwords.words('spanish')#en caso de ser texto en ingles se utiliza 'english
STOPWORDS = nvstrings.to_device(STOPWORDS)

com = text_col_sample['text_clean']
principales = []
for data in com:
  principales.append(data)
  
letras = nvstrings.to_device(principales)

text_col_sample['text_clean'] = nvtext.replace_tokens(letras, STOPWORDS,  ' ')
text_col_sample['text_clean'].to_pandas()

text_col_sample['text_clean'] = text_col_sample['text_clean'].str.replace(r"\s+", ' ',regex=True)
text_col_sample['text_clean'] = text_col_sample['text_clean'].str.strip(' ')
text_col_sample['text_clean'].to_pandas()

# Commented out IPython magic to ensure Python compatibility.
import numpy as np
def get_word_count(str_col):
    """
        returns the count of input strings
    """ 
    ## Tokenize: convierte oraciones en largas listas de palabras


    df = cudf.DataFrame()

    principales = []
    for data in str_col:
      principales.append(data)

    # Tokenizando strings con nvstring y llevandolo al gpu con to_device
      
    letras = nvstrings.to_device(principales)

    df['string'] = nvtext.tokenize(letras)
    
    # Se usa group by para realizar el conteo de palabras por columna
    # Nativamente sera soportado pronto 
    # Mirar para errores: https://github.com/rapidsai/cudf/issues/1951

    df['counts'] = np.dtype('int32').type(0)
    
    res = df.groupby('string').count()
    res = res.reset_index(drop=False).sort_values(by='counts', ascending=False)
    return res.rename({'index':'string'})
    
# %time count_df = get_word_count(df['text'])
count_df.head(10).to_pandas()

# Commented out IPython magic to ensure Python compatibility.
candidatoLista = ['cesarmontufar','davalos','cynthiaviteri','gracielamoraec','jimmyjairala','juancaholguin','lorohomero','luisamaldonadom','pacomoncayo','vickydesintonio']

startTime = time.time()
for data in candidatoLista:
  candidato_df = df[df['author'].str.contains(data)]
  print()
  print('--'+data)
#   %time candidato_count_df = get_word_count(candidato_df['text'])
  print(candidato_count_df.head(5).to_pandas())
  print()



# Commented out IPython magic to ensure Python compatibility.
data_dir = '/content/gdrive/My Drive/GoogleColabProjects/cuDFProject/tweetsCompletos.txt'
data = []
with open(data_dir, 'r') as f:
  lineas = f.readline()
  tweetNombre = lineas.split(',')[2]
  tweetFecha = lineas.split(',')[1]
  tweetTexto = lineas.split(',')[3]

mmf = cudf.DataFrame()

print("\nCUDF  Creation Time:")
# %time mmf['text'] = nvstrings.to_device(tweetTexto)
# %time mmf['nombre'] = nvstrings.to_device(tweetNombre)
mmf['fecha'] = nvstrings.to_device(tweetFecha)
mmf['text'] = nvstrings.to_device(tweetTexto)

mmf.head(2).to_pandas()
