import streamlit as st
import pandas as pd
import easyocr
import numpy as np
from PIL import Image
import os
import re

# Configuration de la page
st.set_page_config(page_title="ScanBordereau", page_icon="🏦")

# --- FONCTIONS DE NETTOYAGE ---

def extraire_montant(liste_textes):
    """Cherche un format monétaire (ex: 120,50) dans les textes détectés."""
    pattern = r'\d+[\.,]\d{2}'
    for texte in liste_textes:
        texte_nettoye = texte.replace(" ", "")
        match = re.search(pattern, texte_nettoye)
        if match:
            return float(match.group().replace(',', '.'))
    return 0.0

def nettoyer_nom(liste_textes):
    """Tente d'isoler l'émetteur en ignorant les mots-clés bancaires."""
    exclusions = ['chèque', 'payez', 'contre', 'euro', 'somme', 'ordre', 'banque']
    for t in liste_textes:
        if len(t) > 3 and not any(ex in t.lower() for ex in exclusions) and not any(c.isdigit() for c in t):
            return t.upper()
    return ""

# --- CHARGEMENT OCR ---

@st.cache_resource
def load_reader():
    # 'fr' pour le français
    return easyocr.Reader(['fr'])

reader = load_reader()

# --- INTERFACE ---

st.title("🏦 Scan de Chèques")
st.write("Prenez une photo du chèque avec la caméra arrière pour l'ajouter au bordereau.")

# Utilisation du File Uploader (déclenche l'appareil photo sur mobile/tablette)
img_file = st.file_uploader("Prendre une photo ou choisir une image", type=['png', 'jpg', 'jpeg'])

if img_file:
    image = Image.open(img_file)
    img_array = np.array(image)
    
    # Affichage de l'aperçu
    st.image(image, caption="Capture prête pour l'analyse", use_container_width=True)
    
    with st.spinner('Analyse intelligente en cours...'):
        results = reader.readtext(img_array, detail=0)
        
        # Extraction automatique
        montant_auto = extraire_montant(results)
        emetteur_auto = nettoyer_nom(results)
        num_detecte = next((t for t in results if len(t) == 7 and t.isdigit()), "")
        
    # Formulaire de validation
    with st.form("form_validation"):
        st.subheader("Vérification des données")
        
        col1, col2 = st.columns(2)
        with col1:
            emetteur = st.text_input("Émetteur", value=emetteur_auto)
        with col2:
            montant = st.number_input("Montant (€)", value=montant_auto, step=0.01, format="%.2f")
            
        banque = st.text_input("Banque")
        num_cheque = st.text_input("N° de chèque", value=num_detecte)
        
        if st.form_submit_button("✅ Enregistrer sur le bordereau"):
            file_path = "bordereau_remise.xlsx"
            
            new_row = {
                "Date": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"),
                "Émetteur": emetteur,
                "Banque": banque,
                "Montant (€)": montant,
                "N° Chèque": num_cheque
            }
            
            if os.path.exists(file_path):
                df = pd.read_excel(file_path)
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            else:
                df = pd.DataFrame([new_row])
                
            df.to_excel(file_path, index=False)
            st.success("Enregistré avec succès !")

# Affichage et Téléchargement
if os.path.exists("bordereau_remise.xlsx"):
    st.divider()
    df_view = pd.read_excel("bordereau_remise.xlsx")
    st.write(f"### Récapitulatif ({len(df_view)} chèques)")
    st.dataframe(df_view)
    
    with open("bordereau_remise.xlsx", "rb") as f:
        st.download_button("📥 Télécharger le fichier Excel", f, "bordereau_remise.xlsx")