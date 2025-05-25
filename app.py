import streamlit as st
import pandas as pd
import os
from utils.clarke_wright import ClarkeWrightOptimizer

# Au début de app.py :
if not os.path.exists("data"):
    os.makedirs("data")
    
# Configuration LE CODE VRAI 
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def save_to_delivery_file(new_results):
    """Sauvegarde les résultats dans livraisons.xlsx en conservant l'historique"""
    file_path = f"{DATA_DIR}/livraisons.xlsx"
    
    # Conversion des dates au format français
    df_new = pd.DataFrame(new_results)
    df_new['Date'] = pd.to_datetime(df_new['Date'], dayfirst=True).dt.strftime('%d/%m/%Y')
    
    # Charger l'historique existant ou créer nouveau fichier 
    if os.path.exists(file_path):
        try:
            df_existing = pd.read_excel(file_path)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        except:
            df_combined = df_new
    else:
        df_combined = df_new
    
    # Sauvegarde avec formatage Excel
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        df_combined.to_excel(writer, index=False)
        
        # Ajustement automatique des colonnes
        worksheet = writer.sheets['Sheet1']
        for col in worksheet.columns:
            max_len = max(len(str(cell.value)) for cell in col)
            worksheet.column_dimensions[col[0].column_letter].width = min(max_len + 2, 30)
    
    return file_path

def main():
    st.set_page_config(page_title="Optimisation des tournées de livraison", layout="centered")
    st.title(" 🚛 Planification des tournées interne COFICAB")
    
    # Upload des données
    uploaded_file = st.file_uploader("Importer clients.xlsx", type="xlsx")
    if not uploaded_file:
        st.info("Veuillez importer le fichier clients")
        return
    
    try:
        df = pd.read_excel(uploaded_file)
        required_cols = {'date_livraison', 'id', 'nom', 'lat', 'lon', 'positions'}
        if not required_cols.issubset(df.columns):
            st.error("Colonnes manquantes dans le fichier")
            return
    except Exception as e:
        st.error(f"Erreur : {str(e)}")
        return

    # Paramètres
    capacity = st.number_input("Capacité des véhicules (positions)", 
                             min_value=1, max_value=50, value=25)

    if st.button("Générer et Sauvegarder", type="primary"):
        with st.spinner("Optimisation en cours..."):
            try:
                optimizer = ClarkeWrightOptimizer(df)
                routes = optimizer.optimize_routes(capacity)
                
                # Préparation des résultats
                results = []
                date_mapping = df.set_index('id')['date_livraison'].astype(str).to_dict()
                
                for i, route in enumerate(routes, 1):
                    metrics = optimizer.calculate_route_metrics(route, capacity)
                    client_ids = route[1:-1]
                    
                    # Formatage des dates existantes depuis le fichier client
                    route_date = date_mapping.get(client_ids[0], '')
                    
                    results.append({
                        'Date': route_date,  # Utilise la date originale du fichier client
                        'Tournée': i,
                        'Clients': metrics['clients_str'],
                        'Positions': f"{sum(df.loc[client_ids, 'positions'])}/{capacity}",
                        'Taux de remplissge(%)': round(metrics['utilization'], 1),
                        'Distance (km)': round(metrics['distance'], 2)
                    })
                
                # Sauvegarde automatique dans livraisons.xlsx
                output_file = save_to_delivery_file(results)
                
                # Affichage des résultats
                st.success(f"✅ {len(routes)} tournées sauvegardées dans:\n{output_file}")
                st.dataframe(
                    pd.DataFrame(results),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Taux (%)": st.column_config.ProgressColumn(
                            format="%.1f%%",
                            min_value=0,
                            max_value=100
                        ),
                        "Date": st.column_config.DateColumn(
                            format="DD/MM/YYYY"
                        )
                    }
                )
            
            except Exception as e:
                st.error(f"Erreur : {str(e)}")

if __name__ == "__main__":
    main()