import streamlit as st
import pandas as pd
import easyocr
import numpy as np
from PIL import Image
import os

# Configuration de la page
st.set_page_config(page_title="ScanBordereau", page_icon="🏦")

# Chargement de l'OCR (mis en cache pour la rapidité)
@st.cache_resource
def load_reader():
    return easyocr.Reader(['fr'])

reader = load_reader()

st.title("🏦 Scan de Chèques")
st.info("Prenez une photo bien éclairée du chèque.")

# Capture caméra
img_file = st.camera_input("Scanner")

if img_file:
    image = Image.open(img_file)
    img_array = np.array(image)
    
    with st.spinner('Analyse du texte...'):
        # Lecture OCR
        results = reader.readtext(img_array, detail=0)
        text_complet = " ".join(results)
        
    # Interface de validation
    with st.form("form_cheque"):
        st.subheader("Validation des données")
        
        # Tentative d'extraction simplifiée de l'émetteur
        val_emetteur = results[0] if len(results) > 0 else ""
        
        emetteur = st.text_input("Émetteur", value=val_emetteur)
        montant = st.number_input("Montant (€)", min_value=0.0, step=0.01)
        banque = st.text_input("Banque")
        num_cheque = st.text_input("N° de chèque")
        
        if st.form_submit_button("Ajouter au bordereau"):
            file_path = "bordereau.xlsx"
            
            new_row = {
                "Date": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"),
                "Émetteur": emetteur,
                "Banque": banque,
                "Montant (€)": montant,
                "N° Chèque": num_cheque
            }
            
            # Gestion du fichier Excel
            if os.path.exists(file_path):
                df = pd.read_excel(file_path)
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            else:
                df = pd.DataFrame([new_row])
                
            df.to_excel(file_path, index=False)
            st.success("Enregistré !")

# Affichage du bordereau actuel et téléchargement
if os.path.exists("bordereau.xlsx"):
    st.divider()
    df_view = pd.read_excel("bordereau.xlsx")
    st.write("### Aperçu du bordereau")
    st.dataframe(df_view)
    
    with open("bordereau.xlsx", "rb") as f:
        st.download_button("📥 Télécharger le fichier Excel", f, "bordereau.xlsx")